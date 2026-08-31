# Access-log variables (generated)

Generated from `src/obs/obs.lu` (`obs.var_table`) by
`tools/lobo-logvars` — NEVER hand-edited. The class-C posture
(report 11): a `log_format` naming a variable whose row is not
`implemented` is a CONFIG-TIME named error, never an empty
string at runtime; a variable with no row at all is the
oracle's own `unknown "x" variable` error, mirrored.

| variable | status | note |
|----------|--------|------|
| `$remote_addr` | implemented | client address; 127.0.0.1 at this pin (loopback-only law; no peer-address builtin — named delta) |
| `$remote_user` | implemented | basic-auth user; lobo has no auth yet, so always the missing value (- / empty) |
| `$time_local` | implemented | common-log clock; lobo logs UTC +0000 (no timezone surface — named delta) |
| `$time_iso8601` | implemented | ISO 8601 clock; lobo logs UTC +00:00 (same named delta) |
| `$request` | implemented | the RAW request line, pre-decode (probed: the oracle logs %XX verbatim and cuts a garbage line at the first CR) |
| `$status` | implemented | the response status lobo wrote |
| `$body_bytes_sent` | implemented | response BODY bytes (headers excluded; probed) |
| `$request_time` | implemented | seconds with 3 decimals; wolf's clock is ms, which is exactly the printed precision |
| `$http_*` | implemented | any REQUEST header ($http_user_agent -> user-agent); missing is - / empty per escape mode (probed) |
| `$upstream_addr` | implemented | the upstream peer host:port the proxy leg used ('' when the request was not proxied) |
| `$upstream_status` | implemented | the upstream response status ('' when not proxied) |
| `$upstream_response_time` | implemented | upstream leg time, seconds with 3 decimals ('' when not proxied) |
| `$msec` | planned(ws12) | epoch seconds with ms decimals; lands with the metrics clock (ws12) |
| `$bytes_sent` | planned(ws12) | full response bytes including headers; needs the writer to count what it wrote |
| `$request_length` | planned(ws12) | request bytes including head and body; needs the reader to count |
| `$connection` | planned(ws12) | connection serial; joins the ws12 counters |
| `$connection_requests` | planned(ws12) | requests on this connection; the keepalive budget counter surfaces at ws12 |
| `$host` | planned(ws12) | effective Host; $http_host carries the header today |
| `$server_name` | planned(ws12) | matched server_name; server selection is host-blind at this pin |
| `$server_port` | planned(ws12) | listening port; joins when the record carries the listener |
| `$server_protocol` | planned(ws12) | request HTTP version; $request carries it raw today |
| `$scheme` | planned(ws12) | http/https; joins when the TLS path joins the step loop (D24 rider) |
| `$remote_port` | planned(ws12) | client port; no peer-address builtin at this pin |
| `$sent_http_*` | planned(ws12) | response headers; needs the writer to record what it sent |
| `$uri` | named_error | the DECODED, normalized path — logging the decoded form leaks the parse and diverges from the oracle line-for-line (contract pitfall); $request carries the raw line, format=json carries structure |
| `$document_uri` | named_error | alias of $uri — same refusal |
| `$args` | named_error | the query string re-assembled from the parse; $request carries it raw |
| `$query_string` | named_error | alias of $args — same refusal |
