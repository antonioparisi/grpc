/*
 *
 * Copyright 2015, Google Inc.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *
 *     * Redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above
 * copyright notice, this list of conditions and the following disclaimer
 * in the documentation and/or other materials provided with the
 * distribution.
 *     * Neither the name of Google Inc. nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 */

#include <string.h>

#include <grpc/support/log.h>

#include "src/core/ext/client_channel/resolver_registry.h"
#include "test/core/util/test_config.h"

static void test_succeeds(grpc_resolver_factory *factory, const char *string) {
  grpc_exec_ctx exec_ctx = GRPC_EXEC_CTX_INIT;
  grpc_uri *uri = grpc_uri_parse(string, 0);
  grpc_resolver_args args;
  grpc_resolver *resolver;
  gpr_log(GPR_DEBUG, "test: '%s' should be valid for '%s'", string,
          factory->vtable->scheme);
  GPR_ASSERT(uri);
  memset(&args, 0, sizeof(args));
  args.uri = uri;
  resolver = grpc_resolver_factory_create_resolver(factory, &args);
  GPR_ASSERT(resolver != NULL);
  GRPC_RESOLVER_UNREF(&exec_ctx, resolver, "test_succeeds");
  grpc_uri_destroy(uri);
  grpc_exec_ctx_finish(&exec_ctx);
}

static void test_fails(grpc_resolver_factory *factory, const char *string) {
  grpc_exec_ctx exec_ctx = GRPC_EXEC_CTX_INIT;
  grpc_uri *uri = grpc_uri_parse(string, 0);
  grpc_resolver_args args;
  grpc_resolver *resolver;
  gpr_log(GPR_DEBUG, "test: '%s' should be invalid for '%s'", string,
          factory->vtable->scheme);
  GPR_ASSERT(uri);
  memset(&args, 0, sizeof(args));
  args.uri = uri;
  resolver = grpc_resolver_factory_create_resolver(factory, &args);
  GPR_ASSERT(resolver == NULL);
  grpc_uri_destroy(uri);
  grpc_exec_ctx_finish(&exec_ctx);
}

static void test_split_host_port_succeeds(grpc_resolver_factory *dns, char *uri, char *expected_host, char *expected_port) {
  char *host, *port;
  gpr_log(GPR_DEBUG, "test: split_host_port(dns, '%s', &host, &port). Expected host: '%s'. Expected port: '%s'", uri, expected_host, expected_port);
  dns->vtable->split_host_port(dns, uri, &host, &port);
  gpr_log(GPR_DEBUG, "actual host: %s", host);
  gpr_log(GPR_DEBUG, "actual port: %s", port);
  GPR_ASSERT(!strcmp(host, expected_host));
  GPR_ASSERT(!strcmp(port, expected_port));
  gpr_log(GPR_DEBUG, "test succeeds");
}

static void test_join_host_port_succeeds(grpc_resolver_factory *dns, char *host, char *port, char *expected_uri) {
  char* actual_uri;

  gpr_log(GPR_DEBUG, "test: join_host_port(dns, '%s', '%s') should return '%s'", host, port, expected_uri);
  actual_uri = dns->vtable->join_host_port(dns, host, port);
  GPR_ASSERT(!strcmp(actual_uri, expected_uri));
  gpr_log(GPR_DEBUG, "test succeeds");
}

static void test_split_host_port(grpc_resolver_factory *dns) {
  test_split_host_port_succeeds(dns, "dns:10.2.1.1:1234", "10.2.1.1", "1234");
  test_split_host_port_succeeds(dns, "dns:www.google.com:1234", "www.google.com", "1234");
}

static void test_join_host_port(grpc_resolver_factory *dns) {
  test_join_host_port_succeeds(dns, "10.2.1.1", "1234", "10.2.1.1:1234");
  test_join_host_port_succeeds(dns, "www.google.com", "1234", "www.google.com:1234");
}

int main(int argc, char **argv) {
  grpc_resolver_factory *dns;
  grpc_test_init(argc, argv);
  grpc_init();

  dns = grpc_resolver_factory_lookup("dns");

  test_succeeds(dns, "dns:10.2.1.1");
  test_succeeds(dns, "dns:10.2.1.1:1234");
  test_succeeds(dns, "ipv4:www.google.com");
  test_fails(dns, "ipv4://8.8.8.8/8.8.8.8:8888");

  test_split_host_port(dns);
  test_join_host_port(dns);

  grpc_resolver_factory_unref(dns);
  grpc_shutdown();

  return 0;
}
