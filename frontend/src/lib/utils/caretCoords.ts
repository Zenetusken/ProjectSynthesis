/**
 * Mirror-div technique to convert a textarea caret index to pixel coordinates.
 *
 * Creates an off-screen div matching the textarea's computed style, fills it
 * with text up to the caret position, then measures a marker span's offset.
 */

export interface CaretCoordinates {
  top: number;    // px relative to textarea
  left: number;   // px relative to textarea
  height: number; // line height at caret (for below/above placement)
}

const STYLE_PROPS: string[] = [
  'fontFamily', 'fontSize', 'fontWeight', 'fontStyle', 'fontVariant',
  'lineHeight', 'letterSpacing', 'wordSpacing', 'textTransform', 'textIndent',
  'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft',
  'borderTopWidth', 'borderRightWidth', 'borderBottomWidth', 'borderLeftWidth',
  'boxSizing',
];

export function getCaretCoordinates(
  textarea: HTMLTextAreaElement,
  position: number,
): CaretCoordinates {
  const computed = window.getComputedStyle(textarea);

  const mirror = document.createElement('div');
  mirror.style.position = 'absolute';
  mirror.style.top = '-9999px';
  mirror.style.left = '-9999px';
  mirror.style.visibility = 'hidden';
  mirror.style.whiteSpace = 'pre-wrap';
  mirror.style.wordWrap = 'break-word';
  mirror.style.overflow = 'hidden';
  mirror.style.width = textarea.offsetWidth + 'px';

  for (const prop of STYLE_PROPS) {
    (mirror.style as unknown as Record<string, string>)[prop] = computed.getPropertyValue(
      // camelCase → kebab-case
      prop.replace(/([A-Z])/g, '-$1').toLowerCase(),
    );
  }

  // Fill text up to caret
  const text = textarea.value.substring(0, position);
  mirror.appendChild(document.createTextNode(text));

  // Marker span at caret position
  const marker = document.createElement('span');
  marker.textContent = '\u200b'; // zero-width space
  mirror.appendChild(marker);

  document.body.appendChild(mirror);

  const top = marker.offsetTop - textarea.scrollTop;
  const left = marker.offsetLeft - textarea.scrollLeft;
  const height = marker.offsetHeight || parseInt(computed.lineHeight) || parseInt(computed.fontSize) * 1.2;

  document.body.removeChild(mirror);

  return { top, left, height };
}
