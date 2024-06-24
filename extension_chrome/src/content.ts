import '../scss/content.scss';

import { render } from './app/App';

const port = chrome.runtime.connect({ name: 'content' });
render(port);
