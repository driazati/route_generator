const status = document.getElementById('status');
const groups = document.getElementById('groups');
const calculate = document.getElementById('calculate');
const file = document.getElementById('file');


class Setting {
  constructor(id, oninput) {
    this.id = id;
    this.value = localStorage.getItem(id);
    this.element = document.getElementById(id);
    if (this.value) {
      this.element.value = this.value;
    } else if (this.element.value) {
      this.set(this.element.value);
    }

    oninput(this);

    this.element.addEventListener('input', (e) => {
      this.set(this.element.value);
      oninput(this);
    });
  }

  get() {
    return this.value;
  }

  set(value) {
    this.value = value;
    localStorage.setItem(this.id, value);
  }
}

const bingSetting = new Setting('bing_api_key', (setting) => {
  setBingAPIKey(setting.get());
  if (setting.value) {
    file.disabled = false;
  } else {
    file.disabled = true;
  }
});

const rowFilterSetting = new Setting('row_filter', (setting) => {
  try {
    setting.fn = new Function('row', `return ${setting.get()}`);
    setting.element.classList.remove('is-invalid');
  } catch (e) {
    setting.element.classList.add('is-invalid');
  }
});

const addressFieldSetting = new Setting('row_filter', (setting) => { });
const targetGroupSizeSetting = new Setting('target_group_size', (setting) => { });
const citySetting = new Setting('city', (setting) => { });
const stateSetting = new Setting('state', (setting) => { });




const FIX_MISSING_ADDRESSES = true;
// const GROUP_SIZE = 5;
// const MAX_GROUP_SIZE = 25;
// const MIN_DELIVERY_DAYS = 30;

const options = document.getElementById('details_options');
const arrow = document.getElementById('arrow');
document.getElementById('details_span').addEventListener('click', () => {
  options.hidden = !options.hidden;
  if (options.hidden) {
    arrow.innerText = '▶';
  } else{
    arrow.innerText = '▼';    
  }
});

const print = console.log

let fileName = null;



document.getElementById('clipboard').addEventListener('click', e => {
  navigator.clipboard.writeText(groups.innerText);
});

file.addEventListener('change',  (e) =>{
  calculate.disabled = false;
  status.innerText = 'waiting to calculate';
  fileName = e.target.files[0];
});

calculate.addEventListener('click', (e) => {
  groups.innerText = '';
  const reader = new FileReader();
  
  reader.onload = function (evt) {
    generator = new RouteGenerator();
    generator.readCsv(evt.target.result, rowFilterSetting.fn, citySetting.get(), stateSetting.get()).then((requesters) => {
      const groups = generator.calculateGroups(requesters, parseInt(targetGroupSizeSetting.get()));
      generator.printGroups(groups, requesters);
    });
  };

  reader.onerror = function (evt) {
    alert("Could not read file");
  };

  reader.readAsText(fileName, "UTF-8");
});


const api_key_input = document.getElementById('bing_api_key');



