import React from 'react';
import { Box, Typography, Divider } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'; // Using Prism for syntax highlighting
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism'; // Example theme

// Component mapping for ReactMarkdown
const components = {
  h1: ({ node, ...props }) => <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 1.5, fontWeight: 600, fontSize: '1.5rem', '&:first-of-type': { mt: 0 }, color: '#ECECF1' }} {...props} />,
  h2: ({ node, ...props }) => <Typography variant="h5" component="h2" sx={{ mt: 2.5, mb: 1.5, fontWeight: 600, fontSize: '1.25rem', '&:first-of-type': { mt: 0 }, color: '#ECECF1' }} {...props} />,
  h3: ({ node, ...props }) => <Typography variant="h6" component="h3" sx={{ mt: 2, mb: 1, fontWeight: 600, fontSize: '1.1rem', color: '#ECECF1' }} {...props} />,
  p: ({ node, ...props }) => <Typography variant="body1" component="p" sx={{ mb: 1.5, whiteSpace: 'pre-wrap', '&:last-child': { mb: 0 }, color: '#ECECF1' }} {...props} />,
  ul: ({ node, ...props }) => <Box component="ul" sx={{ pl: 3, mb: 1.5, color: '#ECECF1', listStyleType: 'disc' }} {...props} />,
  ol: ({ node, ...props }) => <Box component="ol" sx={{ pl: 3, mb: 1.5, color: '#ECECF1' }} {...props} />,
  li: ({ node, ...props }) => <Typography component="li" sx={{ mb: 0.5, color: '#ECECF1' }} {...props} />,
  strong: ({ node, ...props }) => <Box component="strong" sx={{ fontWeight: 700, color: '#FFFFFF' }} {...props} />,
  em: ({ node, ...props }) => <Box component="em" sx={{ fontStyle: 'italic', color: '#FFFFFF' }} {...props} />,
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '');
    return !inline && match ? (
      <SyntaxHighlighter
        style={atomDark}
        language={match[1]}
        PreTag="div"
        {...props}
      >
        {String(children).replace(/\n$/, '')}
      </SyntaxHighlighter>
    ) : (
      <Box
        component="code"
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          color: '#f8f8f2',
          px: '0.4em',
          py: '0.2em',
          borderRadius: '3px',
          fontFamily: 'monospace',
          fontSize: '0.875em',
        }}
        {...props}
      >
        {children}
      </Box>
    );
  },
  blockquote: ({ node, ...props }) => (
    <Box
      component="blockquote"
      sx={{
        borderLeft: '4px solid #10a37f',
        pl: 2,
        py: 0.5,
        my: 1.5,
        color: '#ECECF1',
        backgroundColor: 'rgba(16, 163, 127, 0.1)',
        '& > p': { mb: 0 } // Adjust paragraph margin inside blockquote
      }}
      {...props}
    />
  ),
  a: ({ node, ...props }) => (
    <Box
      component="a"
      target="_blank" // Open links in new tab
      rel="noopener noreferrer" // Security measure
      sx={{
        color: '#10a37f',
        textDecoration: 'underline',
        '&:hover': {
          color: '#0D8C6D',
        },
      }}
      {...props}
    />
  ),
  hr: ({ node, ...props }) => <Divider sx={{ my: 2, borderColor: 'rgba(255,255,255,0.1)' }} {...props} />,
  table: ({ node, ...props }) => (
    <Box component="div" sx={{ overflowX: 'auto', my: 1.5 }}> {/* Add scroll for wide tables */}
      <Box
        component="table"
        sx={{
          width: '100%',
          borderCollapse: 'collapse',
          color: '#ECECF1',
          'th, td': {
            border: '1px solid rgba(255,255,255,0.2)',
            p: 1,
            textAlign: 'left',
          },
          'th': {
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            fontWeight: 600,
          },
        }}
        {...props}
      />
    </Box>
  ),
  // thematicBreak is handled by hr in remarkGfm
};

const MarkdownRenderer = ({ content }) => {
  if (typeof content !== 'string') {
    console.error("MarkdownRenderer received non-string content:", content);
    return <Typography color="error">Error: Invalid content type for rendering.</Typography>;
  }

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]} // Enable GitHub Flavored Markdown (tables, etc.)
      components={components}
      skipHtml={false} // Set to true if you want to disable raw HTML
    >
      {content}
    </ReactMarkdown>
  );
};

export default MarkdownRenderer;
