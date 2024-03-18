from lavague import CommandCenter

commandCenter = CommandCenter(
    chromePath="chrome-linux64/chrome",
    chromedriverPath="chromedriver-linux64/chromedriver",
)
commandCenter.run(
    "https://huggingface.co",
    [
        "Click on the Datasets item on the menu, between Models and Spaces",
        "Click on the search bar 'Filter by name', type 'The Stack', and press 'Enter'",
        "Scroll by 500 pixels",
    ],
)
