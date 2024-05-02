import { NotebookCellData, NotebookData, NotebookEditor, Position, Range } from 'vscode';
import * as vscode from 'vscode';
import * as http from 'http';
import {Mutex, MutexInterface, Semaphore, SemaphoreInterface, withTimeout} from 'async-mutex';
import { log } from 'console';
import { Drive } from '@jupyterlab/services';
import path from 'path';
import * as fs from 'fs';


let edit: vscode.TextEditor | undefined;
let expected_name: string = "";
let editArr: vscode.TextEditor[] = [];

let first = false;
let txt = ""
let target: vscode.TextEditor | undefined = undefined;
let driver: vscode.TextEditor | undefined = undefined;
let driver_doc: vscode.TextDocument
let driver_code = ""
let magic: vscode.TextEditor | undefined = undefined;
let over = false;
let endPosition = undefined
let doc: vscode.TextDocument
let oldcode = ""

const mutex = new Mutex();

function getDriverCode(url: string) {
    const driverCode: string = `from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from lavague import vscode_extension
import lavague
import os.path

chrome_options = Options()

# Turns off GUI
# chrome_options.add_argument("--headless")

chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1600,900")

homedir = os.path.expanduser("~")

# Paths to the chromedriver files
path_linux = f"{homedir}/chromedriver-linux64/chromedriver"
path_testing = f"{homedir}/chromedriver-testing/chromedriver"
path_mac = (
    "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
)

# To avoid breaking change kept legacy linux64 path
if os.path.exists(path_linux):
    chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
    webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")
elif os.path.exists(path_testing):
    if os.path.exists(f"{homedir}/chrome-testing/{path_mac}"):
        chrome_options.binary_location = f"{homedir}/chrome-testing/{path_mac}"
    # Can add support here for other chrome binaries with else if statements
    webdriver_service = Service(f"{homedir}/chromedriver-testing/chromedriver")
else:
    raise FileNotFoundError("Neither chromedriver file exists.")

driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

# Add your target URL as a string argument in the command below
driver.get("${url}")
lavague.vscode_extension.driver = driver`
    return driverCode
}

function defaultPythonCodeExtractor(markdownText: string): string | null {
    // Pattern to match the first ```python ``` code block
    const pattern = /```python([\s\S]*?)```/;

    // Using DOTALL equivalent in TypeScript regex
    const match = markdownText.match(pattern);
    if (match) {
        // Return the first matched group, which is the code inside the ```python ```
        return match[1].trim();
    } else {
        // Return null if no match is found
        return null;
    }
}

const requestListener: http.RequestListener = (req, res) => {
    const fullUrl = new URL(req.url || '', `http://${req.headers.host}`);

    if (fullUrl.pathname === '/push' && req.method === 'POST') {
        const chunks: Uint8Array[] = [];
        
        req.on('data', async (chunk) => {
            console.log("got chunk")
            const data = chunk.toString()
            await mutex.runExclusive(async () => {
                if (target == undefined) {
                    target = edit;
                }
                if (target != undefined) {
                    try {
                    const ret = await target.edit(async (editBuilder) => {
                        if (!first) {
                            const wholeDoc = new Range(
                                target!.document.positionAt(0),
                                target!.document.positionAt(target!.document.getText().length)
                            );
                            editBuilder.delete(wholeDoc)
                            first = true;
                        }
                        endPosition = doc.lineAt(target!.document.lineCount - 1).range.end;
                        editBuilder.insert(endPosition!, data);
                    })
                    }
                    catch (err) {
                        console.log(err)
                    }
                }
            })
        });

        req.on('end', async () => {
            await mutex.runExclusive(async () => {
                if (target == undefined) {
                    target = edit;
                }
                if (target != undefined) {
                    let data = defaultPythonCodeExtractor(doc.getText())
                    oldcode = data ? data : ""
                    try {
                        const ret = await target.edit(async (editBuilder) => {
                            const wholeDoc = new Range(
                                target!.document.positionAt(0),
                                target!.document.positionAt(doc.getText().length)
                            );
                            editBuilder.delete(wholeDoc)
                            endPosition = doc.lineAt(target!.document.lineCount - 1).range.end;
                            if (data)
                                editBuilder.insert(endPosition!, data);
                        })
                    }
                    catch (err) {
                        console.log(err)
                    }
                }
            })
            first = false;
            target = undefined;
            console.log("over")
            res.writeHead(200, { 'Content-Type': 'text/plain' });
            res.end('');
        });

    } 
    else if (fullUrl.pathname === '/export' && req.method === 'POST') {
        req.on('data', async (chunk) => {

        });

        req.on('end', async () => {
            console.log("got export command");
            const result = await vscode.window.showSaveDialog({
                defaultUri: vscode.Uri.file(path.join(vscode.workspace.rootPath == undefined ? getUserHomeFolder() : vscode.workspace.rootPath, 'new_file.py')),
                filters: {
                    'Python Files': ['py']
                }
            });

            if (result) {
                const filePath = result.fsPath;
                const pythonCode = driver_code + "\n\n" + oldcode
                fs.writeFileSync(filePath, pythonCode);
                vscode.window.showInformationMessage(`Python file exported to: ${filePath}`);
            } else {
                // User cancelled the operation
                vscode.window.showInformationMessage('Operation cancelled.');
            }

            res.writeHead(200, { 'Content-Type': 'text/plain' });
            res.end('');
        });

    }
};

function getUserHomeFolder(): string {
    return process.env.HOME || process.env.USERPROFILE || '';
}

const server = http.createServer(requestListener);
const port = 16500;
server.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});

export function activate(context: vscode.ExtensionContext) {
    let editorChangeDisposable = vscode.window.onDidChangeActiveTextEditor(editor => {
        if (editor) {
                editArr = [];
                edit = undefined;
                driver = undefined;
                let edit_old: vscode.TextEditor | undefined = undefined
                let found_magic = false;
                expected_name = editor.document.fileName
                vscode.window.visibleTextEditors.forEach((element) => {
                    if (element!.document.fileName == editor.document.fileName) {
                        editArr.push(element);
                        if (element.document.getText().includes("lavague.vscode_extension.driver = driver")) {
                            console.log("found driver cell")
                            if (driver == undefined) {
                                driver = element;
                                driver_doc = element.document
                                driver_code = driver_doc.getText()
                            }
                        }
                        if (element.document.getText().includes(oldcode) && oldcode.length > 0) {
                            console.log("found cell (old code)")
                            if (edit_old == undefined) {
                                edit_old = element;
                            }
                        }
                        if (element.document.getText().trim().length < 1) {
                            console.log("found cell (empty)")
                            if (edit == undefined) {
                                edit = element;
                            }
                        }
                        else if (element.document.getText().includes("%lavague_exec")) {
                            console.log("found magic command")
                            found_magic = true;
                        }
                    }
                }
                );
                if (!found_magic) {
                    edit = undefined;
                }
                else {
                    if (edit_old != undefined) {
                        edit = edit_old
                        console.log("Picking cell with previously generated code")
                    }
                    else
                        console.log("Picking empty cell")
                    doc = edit!.document
                }
        }
    });

    let editor2 = vscode.window.onDidChangeVisibleTextEditors(editor => {
        if (editor) {
                editArr = [];
                edit = undefined;
                driver = undefined;
                let edit_old: vscode.TextEditor | undefined = undefined
                let found_magic = false;
                vscode.window.visibleTextEditors.forEach((element) => {
                    if (element!.document.fileName == vscode.window.activeTextEditor?.document.fileName) {
                        editArr.push(element);
                        if (element.document.getText().includes("lavague.vscode_extension.driver = driver")) {
                            console.log("found driver cell")
                            if (driver == undefined) {
                                driver = element;
                                driver_doc = element.document
                                driver_code = driver_doc.getText()
                            }
                        }
                        if (element.document.getText().includes(oldcode) && oldcode.length > 0) {
                            console.log("found cell (old code)")
                            if (edit_old == undefined) {
                                edit_old = element;
                            }
                        }
                        if (element.document.getText().trim().length < 1) {
                            console.log("found cell (empty)")
                            if (edit == undefined) {
                                edit = element;
                            }
                        }
                        else if (element.document.getText().includes("%lavague_exec")) {
                            console.log("found magic command")
                            found_magic = true;
                        }
                    }
                }
                );
                if (!found_magic) {
                    edit = undefined;
                }
                else {
                    if (edit_old != undefined) {
                        edit = edit_old
                        console.log("Picking cell with previously generated code")
                    }
                    else
                        console.log("Picking empty cell")
                    doc = edit!.document
                }
        }
    });

	let disposable = vscode.commands.registerCommand('lavague.initDocument', async () => {
        vscode.window.showInputBox({
            prompt: 'Please enter an URL',
            placeHolder: 'URL goes here...'
        }).then(async (input) => {
            if (input) {
                const cell1 = new NotebookCellData(vscode.NotebookCellKind.Markup, "# Driver - Boilerplate code", "markdown")
                const cell2 = new NotebookCellData(vscode.NotebookCellKind.Code, getDriverCode(input), "python")
                const cell_title = new NotebookCellData(vscode.NotebookCellKind.Markup, "# Generate the code", "markdown")
                const cell3 = new NotebookCellData(vscode.NotebookCellKind.Code, "%lavague_exec your_prompt", "python")
                let cell4 = new NotebookCellData(vscode.NotebookCellKind.Code, "", "python")
                var cells: NotebookCellData[];
                cells = [cell1, cell2, cell_title, cell3, cell4];
                const notebook_data = new NotebookData(cells)
                const document = await vscode.workspace.openNotebookDocument(
                    "jupyter-notebook",
                    notebook_data
                );
                document.cellAt(0).executionSummary?.executionOrder?.toString()
                expected_name = document.uri.path
                const editor = await vscode.window.showNotebookDocument(document, {
                    viewColumn: vscode.ViewColumn.One,
                    preserveFocus: false
                });
            } else {
                // User canceled the input
                vscode.window.showInformationMessage('Input canceled.');
            }
        });
	})

	context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
