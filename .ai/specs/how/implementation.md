# Contracts implementation

Follow the [root N:N MVP foundation implementation plan](../../../../.ai/specs/how/n2n-mvp-foundation-implementation-plan.md) and the root governance decision before changing this project.

Implementation begins only after the relevant task is approved. The implementation produces language-neutral JSON Schema, protocol documentation, and compatibility fixtures without creating a shared runtime library.

## Contract validation

The fixture verifier uses the maintained `ajv` 8.20.0 release as its validation dependency. Ajv is MIT licensed and its official documentation provides the dedicated `ajv/dist/2020` export required for JSON Schema Draft 2020-12; the project uses that export rather than the default Draft 07 validator. This version was selected from the upstream release listing on 2026-09-11 after confirming its Draft 2020-12 support and MIT license. The verifier also uses the companion `ajv-formats` 3.0.1 package so UUID and RFC 3339 `date-time` formats are assertions rather than annotations. Both packages are development-only dependencies; Node's standard library loads fixtures and no shared runtime package is produced.

The verifier treats the RPC schema as the fixture entry point, registers the envelope and room-event schemas by stable `$id`, and requires every valid fixture to validate and every invalid fixture to fail. Schema and protocol changes remain spec-first and must be released under the compatibility rule in `protocol.md`.
