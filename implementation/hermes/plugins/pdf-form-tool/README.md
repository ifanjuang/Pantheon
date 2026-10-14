# Native Hermes PDF form tool

This is an adaptation of [LogosIsLife/pdf-tool](https://github.com/LogosIsLife/pdf-tool)
at commit `753a91f61c19bfd0c3b8d69c8025e50ce029780c`. The upstream
`pdf_tool.py` identifies its author as `darlene` and its license as AGPL-3.0.
`pdf_core.py` retains the standalone PyMuPDF helpers from that file; the Open
WebUI `Tools` class has been removed. The Hermes plugin adapter in this
directory is also distributed under AGPL-3.0.

The plugin supplies four Hermes tools: `pdf_form_fields`, `pdf_form_fill`,
`pdf_form_render_page`, and `pdf_form_flatten`. It does not modify the source
PDF. A fill returns a new private file path and a read-back report. A rendered
page is saved as a private PNG or JPEG. Hermes must expose that path to the
user through its normal file attachment mechanism; returning a path alone is
not a chat attachment.

The service account needs PyMuPDF in the same Python environment as Hermes.
No container is needed. Set these environment variables on the native Hermes
service before enabling the plugin:

```text
HERMES_PDF_INPUT_ROOTS=/absolute/readable/attachment/directory
HERMES_PDF_OUTPUT_DIR=/srv/pantheon/hermes/pdf-form-output
```

Create the output directory as the Hermes service account with mode `0700`.
The source must be an absolute PDF path within an input root, or a PDF produced
by the plugin in the output directory. Input files are limited to 50 MB; output
files to 100 MB. Do not include broad roots such as `/` or a whole professional
NAS mount. The plugin does not discover chat attachments on its own; Hermes
must pass their exact local path.

Install through the native `hermes plugins install` workflow for the governed
profile only after the service environment and an attachment path are verified.
This source directory is a candidate; it is not activated by being present in
the Pantheon-Next repository.

For this host, the native gateway is `pantheon-hermes-native.service` and runs
as `pantheon-hermes` with `HERMES_HOME=/srv/pantheon/hermes`. After choosing the
real attachment directory, the remaining deployment steps are:

1. Install PyMuPDF in `/home/pantheon-hermes/hermes-agent/venv` using that
   environment's `pip` under the service account.
2. Create `/srv/pantheon/hermes/pdf-form-output` owned by `pantheon-hermes`,
   mode `0700`.
3. Set the two `HERMES_PDF_*` variables in the native service environment file
   `/etc/pantheon-hermes-native.env` and restart the gateway.
4. Install this directory as a Hermes plugin in `pantheon-governed`, inspect
   its copied manifest and tool list, then enable it.
5. Confirm that the Hermes chat attachment path is reachable by the plugin
   and that a generated PDF can be attached back to the chat. Until this last
   check succeeds, do not describe a returned `output_path` as a download.
