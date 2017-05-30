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

#include <grpc/grpc.h>
#include <grpc/support/alloc.h>

#include "src/core/ext/filters/client_channel/resolver.h"
#include "src/core/ext/filters/client_channel/resolver_registry.h"
#include "src/core/ext/filters/client_channel/resolver/dns/c_ares/grpc_ares_wrapper.h"
#include "src/core/lib/channel/channel_args.h"
#include "src/core/lib/iomgr/combiner.h"
#include "src/core/lib/iomgr/resolve_address.h"
#include "src/core/lib/iomgr/timer.h"
#include "test/core/util/test_config.h"
#include "src/core/lib/support/env.h"
#include "src/core/lib/iomgr/sockaddr_utils.h"

static gpr_mu g_mu;
static grpc_combiner *g_combiner;

static grpc_resolver *create_resolver(grpc_exec_ctx *exec_ctx,
                                      const char *name) {
  grpc_resolver_factory *factory = grpc_resolver_factory_lookup("dns");
  grpc_uri *uri = grpc_uri_parse(exec_ctx, name, 0);
  GPR_ASSERT(uri);
  grpc_resolver_args args;
  memset(&args, 0, sizeof(args));
  args.uri = uri;
  args.combiner = g_combiner;
  grpc_resolver *resolver =
      grpc_resolver_factory_create_resolver(exec_ctx, factory, &args);
  grpc_resolver_factory_unref(factory);
  grpc_uri_destroy(uri);
  return resolver;
}

static void on_done(grpc_exec_ctx *exec_ctx, void *ev, grpc_error *error) {
  gpr_event_set(ev, (void *)1);
}

// interleave waiting for an event with a timer check
static bool wait_loop(int deadline_seconds, gpr_event *ev) {
  while (deadline_seconds) {
    gpr_log(GPR_DEBUG, "Test: waiting for %d more seconds", deadline_seconds);
    if (gpr_event_wait(ev, grpc_timeout_seconds_to_deadline(1))) return true;
    deadline_seconds--;

    grpc_exec_ctx exec_ctx = GRPC_EXEC_CTX_INIT;
    grpc_timer_check(&exec_ctx, gpr_now(GPR_CLOCK_MONOTONIC), NULL);
    grpc_exec_ctx_finish(&exec_ctx);
  }
  return false;
}

typedef struct next_args {
  grpc_resolver *resolver;
  grpc_channel_args **result;
  grpc_closure *on_complete;
} next_args;

static void call_resolver_next_now_lock_taken(grpc_exec_ctx *exec_ctx,
                                              void *arg,
                                              grpc_error *error_unused) {
  next_args *a = arg;
  grpc_resolver_next_locked(exec_ctx, a->resolver, a->result, a->on_complete);
  gpr_free(a);
}

static void call_resolver_next_after_locking(grpc_exec_ctx *exec_ctx,
                                             grpc_resolver *resolver,
                                             grpc_channel_args **result,
                                             grpc_closure *on_complete) {
  next_args *a = gpr_malloc(sizeof(*a));
  a->resolver = resolver;
  a->result = result;
  a->on_complete = on_complete;
  grpc_closure_sched(
      exec_ctx,
      grpc_closure_create(call_resolver_next_now_lock_taken, a,
                          grpc_combiner_scheduler(resolver->combiner, false)),
      GRPC_ERROR_NONE);
}

int main(int argc, char **argv) {
  gpr_setenv("GRPC_DNS_RESOLVER", "ares");
  grpc_test_init(argc, argv);

  grpc_init();

  grpc_ares_init();
  gpr_mu_init(&g_mu);
  g_combiner = grpc_combiner_create(NULL);
  grpc_channel_args *result = NULL;

  grpc_exec_ctx exec_ctx = GRPC_EXEC_CTX_INIT;
  grpc_resolver *resolver = create_resolver(&exec_ctx, "dns:///arecord.test.apolcyntest");
  gpr_event ev1;
  gpr_event_init(&ev1);
  call_resolver_next_after_locking(
      &exec_ctx, resolver, &result,
      grpc_closure_create(on_done, &ev1, grpc_schedule_on_exec_ctx));
  grpc_exec_ctx_flush(&exec_ctx);
  GPR_ASSERT(wait_loop(30,  &ev1));

  GPR_ASSERT(result != NULL);
  GPR_ASSERT(result->num_args == 1);
  grpc_arg arg = result->args[0];
  GPR_ASSERT(arg.type == GRPC_ARG_POINTER);
  GPR_ASSERT(strcmp(arg.key, GRPC_ARG_LB_ADDRESSES) == 0);
  grpc_lb_addresses *addresses = (grpc_lb_addresses*)arg.value.pointer.p;
  GPR_ASSERT(addresses->num_addresses == 1);
  grpc_lb_address addr = addresses->addresses[0];
  char *str;
  grpc_sockaddr_to_string(&str, &addr.address, 1 /* normalize */);
  gpr_log(GPR_INFO, "%s", str);
  GPR_ASSERT(strcmp(str, "1.2.3.4:443") == 0);
  GPR_ASSERT(!addr.is_balancer);

  grpc_channel_args_destroy(&exec_ctx, result);
  GRPC_RESOLVER_UNREF(&exec_ctx, resolver, "test");
  GRPC_COMBINER_UNREF(&exec_ctx, g_combiner, "test");
  grpc_exec_ctx_finish(&exec_ctx);

  grpc_shutdown();
  gpr_mu_destroy(&g_mu);
}
