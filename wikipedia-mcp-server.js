#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} = require('@modelcontextprotocol/sdk/types.js');
const axios = require('axios');

const WIKIPEDIA_API_BASE = 'https://en.wikipedia.org/api/rest_v1';
const WIKIPEDIA_SEARCH_API = 'https://en.wikipedia.org/w/api.php';

class WikipediaServer {
  constructor() {
    this.server = new Server(
      {
        name: 'wikipedia-mcp-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'wikipedia_search',
            description: 'Search Wikipedia articles by query',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Search query for Wikipedia articles',
                },
                results: {
                  type: 'number',
                  description: 'Number of search results to return (default: 5)',
                  default: 5,
                },
              },
              required: ['query'],
            },
          },
          {
            name: 'wikipedia_summary',
            description: 'Get summary of a Wikipedia article',
            inputSchema: {
              type: 'object',
              properties: {
                title: {
                  type: 'string',
                  description: 'Title of the Wikipedia article',
                },
                sentences: {
                  type: 'number',
                  description: 'Number of sentences in summary (default: 3)',
                  default: 3,
                },
              },
              required: ['title'],
            },
          },
          {
            name: 'wikipedia_content',
            description: 'Get full content of a Wikipedia article',
            inputSchema: {
              type: 'object',
              properties: {
                title: {
                  type: 'string',
                  description: 'Title of the Wikipedia article',
                },
              },
              required: ['title'],
            },
          },
          {
            name: 'wikipedia_page_info',
            description: 'Get detailed information about a Wikipedia page',
            inputSchema: {
              type: 'object',
              properties: {
                title: {
                  type: 'string',
                  description: 'Title of the Wikipedia article',
                },
              },
              required: ['title'],
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'wikipedia_search':
            return await this.handleSearch(args);
          case 'wikipedia_summary':
            return await this.handleSummary(args);
          case 'wikipedia_content':
            return await this.handleContent(args);
          case 'wikipedia_page_info':
            return await this.handlePageInfo(args);
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        throw new McpError(
          ErrorCode.InternalError,
          `Error executing ${name}: ${error.message}`
        );
      }
    });
  }

  async handleSearch(args) {
    const { query, results = 5 } = args;

    try {
      const response = await axios.get(WIKIPEDIA_SEARCH_API, {
        params: {
          action: 'query',
          list: 'search',
          srsearch: query,
          srlimit: results,
          format: 'json',
        },
      });

      const searchResults = response.data.query.search;

      if (!searchResults || searchResults.length === 0) {
        return {
          content: [
            {
              type: 'text',
              text: `No results found for query: ${query}`,
            },
          ],
        };
      }

      let resultText = `Wikipedia search results for '${query}':\n\n`;
      searchResults.forEach((result, index) => {
        resultText += `${index + 1}. ${result.title}\n`;
        if (result.snippet) {
          resultText += `   ${result.snippet.replace(/<[^>]*>/g, '')}\n`;
        }
        resultText += '\n';
      });

      return {
        content: [
          {
            type: 'text',
            text: resultText,
          },
        ],
      };
    } catch (error) {
      throw new McpError(
        ErrorCode.InternalError,
        `Wikipedia search failed: ${error.message}`
      );
    }
  }

  async handleSummary(args) {
    const { title, sentences = 3 } = args;

    try {
      const response = await axios.get(`${WIKIPEDIA_API_BASE}/page/summary/${encodeURIComponent(title)}`);
      const summary = response.data;

      if (!summary || summary.type === 'disambiguation') {
        return {
          content: [
            {
              type: 'text',
              text: `Multiple articles found for '${title}'. Please be more specific.`,
            },
          ],
        };
      }

      let summaryText = `Summary of '${summary.title}':\n\n`;
      if (summary.extract) {
        const sentenceArray = summary.extract.split('. ');
        const limitedSummary = sentenceArray.slice(0, sentences).join('. ');
        summaryText += limitedSummary;
        if (sentenceArray.length > sentences) {
          summaryText += '.';
        }
      }

      if (summary.content_urls && summary.content_urls.desktop) {
        summaryText += `\n\nURL: ${summary.content_urls.desktop.page}`;
      }

      return {
        content: [
          {
            type: 'text',
            text: summaryText,
          },
        ],
      };
    } catch (error) {
      if (error.response && error.response.status === 404) {
        return {
          content: [
            {
              type: 'text',
              text: `No Wikipedia page found for '${title}'`,
            },
          ],
        };
      }
      throw new McpError(
        ErrorCode.InternalError,
        `Failed to get summary: ${error.message}`
      );
    }
  }

  async handleContent(args) {
    const { title } = args;

    try {
      const response = await axios.get(WIKIPEDIA_SEARCH_API, {
        params: {
          action: 'query',
          prop: 'extracts',
          titles: title,
          explaintext: true,
          format: 'json',
        },
      });

      const pages = response.data.query.pages;
      const pageId = Object.keys(pages)[0];
      const page = pages[pageId];

      if (pageId === '-1' || !page.extract) {
        return {
          content: [
            {
              type: 'text',
              text: `No Wikipedia page found for '${title}'`,
            },
          ],
        };
      }

      let content = `Title: ${page.title}\n`;
      content += `Page ID: ${page.pageid}\n\n`;
      content += `Content:\n${page.extract}`;

      return {
        content: [
          {
            type: 'text',
            text: content,
          },
        ],
      };
    } catch (error) {
      throw new McpError(
        ErrorCode.InternalError,
        `Failed to get content: ${error.message}`
      );
    }
  }

  async handlePageInfo(args) {
    const { title } = args;

    try {
      const response = await axios.get(WIKIPEDIA_SEARCH_API, {
        params: {
          action: 'query',
          prop: 'info|categories|links|images',
          titles: title,
          inprop: 'url',
          cllimit: 10,
          pllimit: 10,
          imlimit: 5,
          format: 'json',
        },
      });

      const pages = response.data.query.pages;
      const pageId = Object.keys(pages)[0];
      const page = pages[pageId];

      if (pageId === '-1') {
        return {
          content: [
            {
              type: 'text',
              text: `No Wikipedia page found for '${title}'`,
            },
          ],
        };
      }

      let info = `Title: ${page.title}\n`;
      info += `Page ID: ${page.pageid}\n`;
      if (page.fullurl) {
        info += `URL: ${page.fullurl}\n`;
      }

      if (page.categories) {
        const categories = page.categories.map(cat => cat.title.replace('Category:', ''));
        info += `Categories: ${categories.join(', ')}\n`;
      }

      if (page.links) {
        info += `Links count: ${page.links.length}\n`;
      }

      if (page.images) {
        info += `Images count: ${page.images.length}\n`;
        if (page.images.length > 0) {
          info += `First image: ${page.images[0].title}\n`;
        }
      }

      return {
        content: [
          {
            type: 'text',
            text: info,
          },
        ],
      };
    } catch (error) {
      throw new McpError(
        ErrorCode.InternalError,
        `Failed to get page info: ${error.message}`
      );
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Wikipedia MCP server running on stdio');
  }
}

const server = new WikipediaServer();
server.run().catch(console.error);