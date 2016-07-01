# Copyright 2015, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

require_relative '../grpc'

# GRPC contains the General RPC module.
module GRPC
  module Core
    # Wrapper for grpc_compression_options in core
    # This class is defined as a C extension but is reopened here
    # to add the initialization logic.
    #
    # This class wraps a GRPC core compression options.
    #
    # It can be used to create a channel argument key-value hash
    # with keys and values that correspond to the compression settings
    # provided here.
    #
    # call-seq:
    #   options = CompressionOptions.new(
    #     default_level: low,
    #     disabled_algorithms: [:gzip])
    #
    # channel_args = Hash.new[...]
    # channel_args_with_args_for_compression_settings = channel_args.merge(options)
    class CompressionOptions
      # Initializes a CompresionOptions instance
      # Starts out with all available compression algorithms enabled by default
      #
      # @param default_level [String | Symbol] one of nil, 'none', 'low', 'medium', 'high'
      # @param default_algorithm [String | Symbol] one of nil, 'identity', 'gzip', or 'deflate'
      # @param disabled_algorithms [Array<String, Symbol>] can contain 'identity', 'gzip', or 'deflate'
      def initialize(default_algorithm: nil,
                     default_level: nil,
                     disabled_algorithms: [])
        disabled_algorithms.each do |algorithm|
          if default_algorithm == algorithm
            raise ArgumentError("default algorithm #{default_algorithm} " \
              "is included in disabled_algorithms")
          end
        end

        set_default_algorithm(default_algorithm) unless default_algorithm.nil?
        set_default_level(default_level) unless default_level.nil?
        disable_algorithms(*disabled_algorithms) unless disabled_algorithms.empty?
      end

      def to_s
        to_hash.to_s
      end
    end
  end
end
