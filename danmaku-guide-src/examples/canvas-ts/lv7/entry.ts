// #region browser-entry
import { mount } from './main';
const canvas = document.createElement('canvas');
document.body.append(canvas);
mount(canvas);
// #endregion
