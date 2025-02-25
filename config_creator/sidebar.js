document.addEventListener("DOMContentLoaded", () => {
    const browserAPI = window.browser || window.chrome;

    document.getElementById('add-field').addEventListener('click', addSection);
    document.getElementById('validate-config').addEventListener('click', validateConfig);
    document.getElementById('save-config').addEventListener('click', saveConfig);
    document.getElementById('highlight-article').addEventListener('click', () =>
        enableHighlightMode(document.getElementById('section-name'))
    );
    addSection();
});

async function validateConfig() {
    const browserAPI = window.browser || window.chrome;
    const configData = saveConfig(false);

    try {
        const [tab] = await browserAPI.tabs.query({ active: true, currentWindow: true });

        if (tab?.id) {
            await browserAPI.scripting.executeScript({
                target: { tabId: tab.id },
                files: ['content.js'],
            });

            browserAPI.tabs.sendMessage(tab.id, { type: 'validate', payload: configData });

            const messageHandler = (message) => {
                console.log("Validation Response:", message);
            };

            browserAPI.runtime.onMessage.addListener(messageHandler);
        } else {
            console.error('No active tab found!');
        }
    } catch (error) {
        console.error('Error validating config:', error.message);
    }
}


function saveConfig(output = true) {
    let configJSON = { "config": {} };
    let configName = "placeholder_name";

    const fieldContainers = document.querySelectorAll('.field-container');



    fieldContainers.forEach((container) => {
        const input = container.querySelector('input');
        const dropdown = container.querySelector('select');
        const label = container.querySelector('label');

        if (input) {
            const xpath = input.value || null;
            let section = dropdown ? dropdown.value : label?.textContent || null;

            if (section === "Article")
                return;

            if (section === "Config name") {
                configName = input.value.endsWith(".json") ? input.value : input.value + ".json";
                return;
            }

            configJSON["config"][section] = {
                "defined-by": [{ "xpath": xpath }],
            }

            const dataSectionContainers = container.querySelector('.data-section');
            if (dataSectionContainers) {
                configJSON["config"][section]["data"] = [];
                Array.from(dataSectionContainers.children).forEach((child) => {
                    const dataSectionInput = child.querySelector('input');
                    const dataSectionDropdown = child.querySelector('select');
                    const dataSectionLabel = child.querySelector('label');
                    const dataSection = dataSectionDropdown ? dataSectionDropdown.value : dataSectionLabel?.textContent || null;
                    configJSON["config"][section]["data"].push({
                        [dataSection]: [{"xpath": dataSectionInput.value}],
                    });
                });
            }
        }
    });

    if (output) {
        const configFile = new Blob([JSON.stringify(configJSON)], { type: 'text/plain' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(configFile);
        a.download = configName;
        a.click();
        a.remove();
    } else {
        return configJSON;
    }
}

function removeSection(fieldDiv) {
    fieldDiv.remove();
}

function onSectionChange(e) {
    const newSectionName = e.target.value;
    const newDataSectionOptions = getDataSectionOptions(newSectionName);
    const sectionContainer = e.target.parentNode;

    Array.from(sectionContainer.children).forEach((child) => {
        if (child.classList.contains("data-section")) {
            sectionContainer.removeChild(child);
        }
    });

    if (newDataSectionOptions.length === 0) return;

    const dataSection = document.createElement('div');
    dataSection.className = 'data-section';

    newDataSectionOptions.forEach((option) => {
        const row = document.createElement('div');
        row.className = 'data-section-row-container';

        const label = document.createElement('label');
        label.className = 'data-section-label';
        label.textContent = option;

        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'XPath';
        input.readOnly = true;

        const highlightButton = document.createElement('button');
        highlightButton.textContent = 'Highlight';
        highlightButton.addEventListener('click', () => enableHighlightMode(input));

        row.appendChild(label);
        row.appendChild(input);
        row.appendChild(highlightButton);
        dataSection.appendChild(row);
    });

    sectionContainer.appendChild(dataSection);
}

function getDataSectionOptions(sectionName) {
    const options = {
        'sections': ['headers'],
        'sub-sections': ['headers'],
        'tables': ['caption', 'table-content', 'title', 'footer', 'table-row', 'header-row', 'header-element'],
        'references': ['title', 'journal', 'volume']
    };

    return options[sectionName] || [];
}

function addSection() {
    const container = document.getElementById('form-container');

    const fieldDiv = document.createElement('div');
    fieldDiv.className = 'field-container';

    const dropdown = document.createElement('select');
    dropdown.className = 'section-dropdown';
    const options = [
        'Abbreviations-table', 'Acknowledgements', 'Figures', 'Keywords',
        'Paragraphs', 'Sections', 'Sub-sections', 'Tables', 'Title'
    ];

    options.forEach((option) => {
        const optionElement = document.createElement('option');
        optionElement.value = option.toLowerCase().replace(/ & /g, '-').replace(/ /g, '-');
        optionElement.textContent = option;
        dropdown.appendChild(optionElement);
    });

    dropdown.addEventListener('change', onSectionChange);

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'XPath';
    input.readOnly = true;

    const highlightButton = document.createElement('button');
    highlightButton.textContent = 'Highlight';
    highlightButton.addEventListener('click', () => enableHighlightMode(input));

    const removeButton = document.createElement('button');
    removeButton.textContent = 'Remove';
    removeButton.addEventListener('click', () => removeSection(fieldDiv));

    fieldDiv.appendChild(dropdown);
    fieldDiv.appendChild(input);
    fieldDiv.appendChild(highlightButton);
    fieldDiv.appendChild(removeButton);
    container.appendChild(fieldDiv);
}

async function enableHighlightMode(input) {
    try {
        const browserAPI = window.browser || window.chrome;
        const [tab] = await browserAPI.tabs.query({ active: true, currentWindow: true });

        if (tab?.id) {
            await browserAPI.scripting.executeScript({
                target: { tabId: tab.id },
                files: ['content.js'],
            });

            browserAPI.tabs.sendMessage(tab.id, { type: 'enable-highlight-mode' });

            const messageHandler = (message) => {
                if (message.type === 'xpath-selected') {
                    input.value = message.xpath;
                    browserAPI.runtime.onMessage.removeListener(messageHandler);
                }
            };

            browserAPI.runtime.onMessage.addListener(messageHandler);
        } else {
            console.error('No active tab found!');
        }
    } catch (error) {
        console.error('Error enabling highlight mode:', error.message);
    }
}
