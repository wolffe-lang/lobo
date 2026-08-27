# TEST key material — never trust, never deploy

Every key and certificate in this directory (and in
`tests/config-corpus/certbot-vhost/live/`) is TEST material generated
for the ws05 rig with the host openssl (Ed25519 CA "wws TEST CA",
leaf CN=localhost SAN DNS:localhost; an RSA pair kept ONLY to prove
the named-unsupported refusal; `reordered.pem` is the fullchain with
the blocks deliberately swapped for the leaf-first error's test;
`other.key` is a second Ed25519 key for the pair-mismatch error's
test). The private keys are PUBLIC by construction — they are in a
git tree. Nothing here is trusted by anything outside this
repository's test harness: the interop harness injects the CA only
into its own openssl invocations (env/flag), never a system store.
