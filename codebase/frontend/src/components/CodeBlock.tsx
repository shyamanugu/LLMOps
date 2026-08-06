/** Monospace code/preformatted block with an optional copy-to-clipboard button. */
import { useCallback, useState } from 'react';

interface CodeBlockProps {
  code: string;
  language?: string;
  copyable?: boolean;
}

export function CodeBlock({
  code,
  language = 'text',
  copyable = true,
}: CodeBlockProps): JSX.Element {
  const [copied, setCopied] = useState(false);

  const onCopy = useCallback(() => {
    void navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    });
  }, [code]);

  return (
    <div className="code-block">
      <div className="code-block__bar">
        <span>{language}</span>
        {copyable ? (
          <button
            type="button"
            className="code-block__copy"
            onClick={onCopy}
            aria-label="Copy code to clipboard"
          >
            {copied ? 'Copied' : 'Copy'}
          </button>
        ) : null}
      </div>
      <pre>
        <code>{code}</code>
      </pre>
    </div>
  );
}
