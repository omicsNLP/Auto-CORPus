let highlightMode = false;
let selectedElement = null;
let hierarchyStack = [];
let panel = null;

function injectCSS() {
  if (!document.querySelector("link[href*='style.css']")) {
    const style = document.createElement('link');
    style.rel = 'stylesheet';
    style.type = 'text/css';
    style.href = (typeof browser !== 'undefined' ? browser : chrome).runtime.getURL('style.css');
    document.head.appendChild(style);
  }
}

document.addEventListener('mouseover', (e) => {
  if (highlightMode) {
    e.target.classList.add("config-creator-target");
    injectCSS();
  }
});

document.addEventListener('mouseout', (e) => {
  if (highlightMode) {
    e.target.classList.remove("config-creator-target");
  }
});

document.addEventListener('click', (e) => {
  if (highlightMode) {
    if (e.target.closest('[data-ignore-xpath]')) return;

    e.preventDefault();
    e.stopPropagation();

    disableHighlightMode();
    clearHighlightedElements();

    selectedElement = e.target;
    hierarchyStack = [selectedElement];

    highlightElement(selectedElement);
    showNavigationPanel();
  }
});

function showNavigationPanel() {
  if (panel) panel.remove();

  panel = document.createElement('div');
  panel.setAttribute('data-ignore-xpath', 'true');
  Object.assign(panel.style, {
    position: 'fixed', bottom: '10px', left: '50%', transform: 'translateX(-50%)',
    background: 'white', border: '1px solid black', padding: '10px', zIndex: '9999',
    display: 'flex', gap: '10px'
  });

  const buttons = [
    { text: 'Up', action: moveUp },
    { text: 'Down', action: moveDown },
    { text: '✔', action: confirmSelection }
  ];

  buttons.forEach(({ text, action }) => {
    const button = document.createElement('button');
    button.innerText = text;
    button.setAttribute('data-ignore-xpath', 'true');
    button.addEventListener('click', action);
    panel.appendChild(button);
  });

  document.body.appendChild(panel);
}

function enableHighlightMode() {
  highlightMode = true;
  showNavigationPanel();
  clearHighlightedElements();

  const queryTabs = (typeof browser !== 'undefined' ? browser : chrome).tabs.query({ active: true, currentWindow: true });
  queryTabs.then(([tab]) => {
    if (tab && tab.id) {
      (typeof browser !== 'undefined' ? browser : chrome).scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js'],
      }).then(() => {
        (typeof browser !== 'undefined' ? browser : chrome).runtime.sendMessage({ type: 'enable-highlight-mode' }).catch(err => console.warn("Messaging failed:", err));
      }).catch(err => console.error("Error injecting script:", err.message));
    }
  }).catch(err => console.error("Tab query failed:", err));
}

function moveUp() {
  if (selectedElement && selectedElement.parentElement) {
    clearHighlightedElements();
    selectedElement = selectedElement.parentElement;
    hierarchyStack.push(selectedElement);
    highlightElement(selectedElement);
  }
}

function moveDown() {
  if (hierarchyStack.length > 1) {
    clearHighlightedElements();
    hierarchyStack.pop();
    selectedElement = hierarchyStack[hierarchyStack.length - 1];
    highlightElement(selectedElement);
  }
}

function confirmSelection() {
  if (!selectedElement) {
    console.error("No element selected!");
    return;
  }
  updateXPath();

  clearHighlightedElements();
  if (panel) panel.remove();
  disableHighlightMode();
}

function sendMessageToBackground(message) {
  const runtime = typeof browser !== 'undefined' ? browser.runtime : chrome.runtime;
  runtime.sendMessage(message, () => {
    if (chrome.runtime.lastError) {
      console.warn("Message failed:", chrome.runtime.lastError);
    }
  });
}

function updateXPath() {
  sendMessageToBackground({ type: 'xpath-selected', xpath: generateGeneralizedXPath(selectedElement) });
}

function highlightElement(element) {
  element.classList.add("config-creator-target");
  injectCSS();
}

function disableHighlightMode() {
  highlightMode = false;
}

function clearHighlightedElements() {
  document.querySelectorAll('.config-creator-target').forEach(el => el.classList.remove('config-creator-target'));
}

function generateGeneralizedXPath(element) {
  let path = '';
  while (element && element.nodeType === Node.ELEMENT_NODE) {
    const tagName = element.nodeName.toLowerCase();
    if (element.classList.length > 1) {
      const className = Array.from(element.classList).filter(cls => cls !== 'config-creator-target')[0];
      path = `${tagName}[contains(@class, '${className}')]` + (path ? `/${path}` : '');
    } else {
      path = `${tagName}` + (path ? `/${path}` : '');
    }
    if (tagName === 'html' || tagName === 'body') {
      path = `//${path}`;
      break;
    }
    element = element.parentNode;
  }
  return path;
}

((typeof browser !== 'undefined' ? browser.runtime : chrome.runtime).onMessage.addListener)((message) => {
  if (message.type === 'enable-highlight-mode') enableHighlightMode();
});
