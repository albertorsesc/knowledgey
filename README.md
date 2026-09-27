# knowledgey

Collect what you read into one local Markdown library.

`kg` pulls articles from RSS and Atom feeds, takes pasted text, converts everything to Markdown, files it under categories you define, and keeps it as plain files on your disk. No account, no server, nothing to run in the background.

> Early project. Storage is a set of JSON files today and is designed to move to a database. The command surface is usable but may still change before 1.0.

## Install

Requires Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:albertorsesc/knowledgey.git
cd knowledgey
uv sync
uv run kg version
```

To get `kg` on your PATH instead of prefixing every call with `uv run`:

```bash
uv tool install .
```

## Quick start

```bash
# 1. Declare the categories you file things under. The vocabulary is closed on purpose.
kg category add "MLOps"
kg category add "RAG"

# 2. Register a feed and file it under a category.
kg source add --name "Simon Willison" --feed-url https://simonwillison.net/atom/everything/ --category mlops

# 3. Pull every registered source. One row per source, failures do not stop the others.
kg source fetch

# 4. Browse and read.
kg list --category mlops
kg show 3fb5c            # any unique prefix of an id from the list
kg show 3fb5c --raw      # the stored Markdown, untouched, ready to pipe into a file

# 5. Paste your own notes into the same library.
kg add --title "Reading notes" --category rag --file notes.md
cat notes.md | kg add --title "Reading notes" --category rag   # same thing via stdin
```

Every command accepts `--json` for machine-readable output.

## Concepts

**Documents** are the unit of storage: a title, a Markdown body, where it came from, and optional URL, authors, publish date, source and categories. A document's identity is a hash of its URL when it has one, otherwise a hash of its content. Adding the same thing twice is a no-op reported as a duplicate, so fetching a feed repeatedly only stores what is new.

**Sources** are feeds you fetch from repeatedly. Each has a slug derived from its name, a feed URL, the categories it files documents under, an enabled flag, and the time it was last fetched successfully. Documents ingested through a source inherit its slug and categories.

**Categories** are a closed vocabulary. You declare them once, then sources and documents can only use declared ones. Spelling variants that differ only in case or separators (`MLOps`, `ml-ops`, `ML Ops`) resolve to the same category, so a typo cannot silently create a second one. Synonyms do not merge: `ops` and `operations` stay separate.

## Commands

| Command | What it does |
| --- | --- |
| `kg add -t TITLE [-f FILE] [--url URL] [--author NAME]... [-c CATEGORY]...` | Store a file, or standard input when `-f` is absent, as a document. |
| `kg fetch URL` | Fetch one feed by URL and store its entries. Useful for feeds you do not want to register. |
| `kg list [-c CATEGORY]` | List stored documents, newest first. |
| `kg show REF [--raw]` | Show one document. `REF` is the id or any prefix that matches exactly one. |
| `kg chunks REF` | Show how a document splits into chunks for indexing: index, chunk id, size, first line. |
| `kg category add LABEL` | Declare a category. Re-adding a spelling variant reports the existing one. |
| `kg category list` | List declared categories. |
| `kg source add -n NAME -u FEED_URL [-c CATEGORY]...` | Register a feed. Categories must already be declared. |
| `kg source list [-c CATEGORY]` | List registered sources, including disabled ones. |
| `kg source fetch [-c CATEGORY]` | Fetch every enabled source. Exit code 1 if any source failed. |
| `kg config` | Show the active configuration. |
| `kg version` | Show the installed version. |

Short flags: `-t` title, `-f` file, `-c` category, `-n` name, `-u` feed URL.

## Configuration

| Setting | Default | Meaning |
| --- | --- | --- |
| `KG_DATA_DIR` | `~/.knowledgey` | Directory holding the library. |

Set it in the environment or in a `.env` file in the working directory (see `.env.example`). `kg config` prints what is in effect.

The data directory contains three files, each a JSON object keyed by id or slug:

```
documents.json
sources.json
categories.json
```

Writes go to a temporary file first and are renamed into place, so an interrupted run cannot leave a half-written library. Back it up by copying the directory.

## Output and exit codes

Text output is a table for lists and `key: value` lines for single results. `--json` prints the same data as JSON.

| Exit code | Meaning |
| --- | --- |
| 0 | Success. |
| 1 | A handled error: unreachable feed, invalid input, unknown category, ambiguous reference. One line on stderr, no traceback. |
| 2 | The command line did not parse: missing argument, unknown option. |

## How ingestion works

- Feeds are parsed with `feedparser`, so both RSS and Atom work. Input that is not a feed, such as an HTML page, is rejected with a clear message.
- Entries without a link or without a body are skipped. When an entry carries both a summary and full content, the full content wins.
- `<script>` and `<style>` blocks are removed before conversion. The remaining HTML becomes Markdown with `#` headings and `*` bullets, and blank lines are collapsed.
- Feed dates become timezone-aware UTC datetimes.
- A source is stamped as fetched only when its feed came through and was parsed. A network error or a non-feed response leaves the stamp alone and reports the error in that source's row.

## How chunking works

Search will run over chunks, not whole documents: one vector cannot carry the several topics a long article covers. `kg chunks REF` previews the split so you can see what an index will hold.

- Chunks are at most 4000 characters with a 200 character overlap, so a sentence cut at a boundary still appears whole in one of the two chunks.
- Splitting uses LangChain's `RecursiveCharacterTextSplitter` with a Markdown-aware separator order: horizontal rules, blank lines, code fences, `##` and `#` headings, bold runs, line breaks, sentence ends, spaces, characters. The splitter takes the most structural boundary that keeps a piece under the limit, so a heading starts a chunk and a code block is not cut mid-function.
- Each chunk has a stable id derived from its document, position and text. Re-chunking unchanged content yields the same ids, which is what makes incremental indexing possible later.
- The size unit is pluggable: characters today, tokens once an embedding model's tokenizer is in play.

## Development

```bash
make install     # uv sync
make check       # format, lint, type-check, tests
make test        # pytest only
make lint        # ruff check
make format      # ruff format
make typecheck   # mypy, strict
```

The gate is `ruff` with the `E F I B UP SIM` rule sets, `mypy --strict` over `src` and `tests`, and `pytest`. Everything is expected to pass before a commit.

### Layout

```
src/knowledgey/
  domain/              models and value objects: document, source, category, slug, chunk
  application/         use cases (ingest, registry, library) and the ports they depend on
  infrastructure/
    persistence/       JSON file store behind the Repository port
    content/           HTTP fetching, RSS and Atom parsing, HTML to Markdown
    chunking/          LangChain-backed splitter
    cli/               Typer application and Rich rendering
    config.py          settings, KG_ prefix
tests/                 mirrors src: domain/, application/, infrastructure/
```

The dependency rule: `domain` imports nothing above it and no third-party package except pydantic; `application` imports `domain` and its own ports; `infrastructure` implements the ports and is the only layer that knows about vendors. Swapping a vendor means one new module under `infrastructure/`, wired in one place.

### Design rules

- Domain modules never import Typer or Rich. A test fails the build if one does.
- Storage sits behind a `Repository` protocol. `JsonFileStore` is the first adapter and is written to be replaced.
- Models are frozen Pydantic models. Every result object exposes `as_dict()`, so one renderer serves both text and JSON.
- Errors reach the user as one line. A traceback in normal use is a bug.

### Contributing

One feature per commit, with its tests. Run `make check` before opening a pull request. Bug reports with the failing command and its `--json` output are the easiest to act on.

## Roadmap

Ideas, not commitments, in no particular order:

- Embeddings and a local vector index over chunks, with hybrid keyword plus semantic search (`kg index`, `kg search`).
- Answers grounded in retrieved chunks, with the LLM provider behind a port (`kg ask`).
- An HTTP API exposing the same operations.
- A SQLite store behind the same `Repository` protocol.
- Fetching the full article when a feed only carries a summary.
- Enabling, disabling and removing sources from the command line.
- Falling back to the feed-level author when entries carry none.
