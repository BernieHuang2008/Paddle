# Copyright (c) 2023 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from dygraph_to_static_utils_new import (
    Dy2StTestBase,
    test_ast_only,
)

import paddle
from paddle.base import core
from paddle.jit.dy2static import (
    partial_program,
    pir_partial_program,
    program_translator,
)


class TestPartiaProgramLayerHook(Dy2StTestBase):
    # TODO(dev): Remove this after PIR becomes the default.
    def setUp(self):
        self._hook = partial_program.PartialProgramLayerHook()

    @test_ast_only
    def test_before_append_backward(self):
        self.assertIsNone(self._hook.before_append_backward(None))

    @test_ast_only
    def test_after_append_backward(self):
        self.assertIsNone(self._hook.after_append_backward(None, 0))

    @test_ast_only
    def test_after_infer(self):
        self.assertIsNone(self._hook.after_infer(None))


class TestPirPartiaProgramLayerHook(Dy2StTestBase):
    def setUp(self):
        self._hook = pir_partial_program.PartialProgramLayerHook()

    @test_ast_only
    def test_before_append_backward(self):
        self.assertIsNone(self._hook.before_append_backward(None, None))

    @test_ast_only
    def test_after_append_backward(self):
        self.assertIsNone(self._hook.after_append_backward(None, None, 0))

    @test_ast_only
    def test_after_infer(self):
        self.assertIsNone(self._hook.after_infer(None))


class TestPrimHook(Dy2StTestBase):
    def setUp(self):
        core._set_prim_all_enabled(False)

        def f():
            return paddle.nn.functional.dropout(paddle.rand((1,)))

        concrete_program, partial_program = paddle.jit.to_static(
            f, full_graph=True
        ).get_concrete_program()
        self._hook = program_translator.PrimHooker(
            concrete_program.main_program, None
        )
        self._forward = partial_program.forward_program
        self._whole = partial_program._train_program

        core._set_prim_all_enabled(True)

    def tearDown(self):
        core._set_prim_all_enabled(False)

    @test_ast_only
    def test_before_append_backward(self):
        self._hook.before_append_backward(self._forward)
        self.assertNotIn(
            'dropout', tuple(op.type for op in self._forward.blocks[0].ops)
        )

    @test_ast_only
    def test_after_append_backward(self):
        self._hook.after_append_backward(self._whole, 0)
        self.assertNotIn(
            'dropout_grad', tuple(op.type for op in self._whole.blocks[0].ops)
        )


class TestPirPrimHook(Dy2StTestBase):
    def setUp(self):
        core._set_prim_all_enabled(True)
        with paddle.pir_utils.IrGuard():
            paddle.disable_static()

            def f():
                return paddle.nn.functional.dropout(paddle.rand((1,)))

            concrete_program, partial_program_layer = paddle.jit.to_static(
                f, full_graph=True
            ).get_concrete_program()
            self._hook = program_translator.PirPrimHooker(
                concrete_program.main_program, None
            )
            self.partial_program_layer = partial_program_layer

    def tearDown(self):
        core._set_prim_all_enabled(False)

    @test_ast_only
    def test_before_append_backward(self):
        with paddle.pir_utils.IrGuard():
            program = self.partial_program_layer.program

            self._hook.before_append_backward(
                program.forward_program,
                program.out_values,
            )
            self.assertNotIn(
                'dropout',
                tuple(
                    op.name()
                    for op in program.forward_program.global_block().ops
                ),
            )

    @test_ast_only
    def test_after_append_backward(self):
        with paddle.pir_utils.IrGuard():
            program_ = self.partial_program_layer.train_program
            train_program = program_.program

            (
                program,
                forward_end_idx,
                targets,
            ) = self._hook.after_append_backward(
                train_program, program_.out_values, 0
            )
            self.assertNotIn(
                'pd_op.dropout_grad',
                tuple(op.name() for op in train_program.global_block().ops),
            )


if __name__ == '__main__':
    unittest.main()
