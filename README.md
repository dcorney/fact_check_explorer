# Fact Check Explorer

Explore Google's Fact Check Explorer

Google provides a [Fact Check Explorer tool](https://toolbox.google.com/factcheck/explorer) that indexes checks published by many fact checking organizations round the world. They also provide an open [API](https://developers.google.com/fact-check/tools/api/).

The `demo.py` script here provides some simple examples of what you can do, including getting a (partial) list of fact checking organizations and getting recent checked claims.

The API doesn't seem to provide access to a full list of fact checkers - you could make your own list from the [IFCN Signatories](https://ifcncodeofprinciples.poynter.org/signatories) easily enough. My code searches for some common terms and builds a list of fact checkers, but it's not comprehensive.
