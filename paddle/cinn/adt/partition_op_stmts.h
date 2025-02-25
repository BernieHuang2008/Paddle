// Copyright (c) 2023 PaddlePaddle Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#pragma once

#include "paddle/cinn/adt/adt.h"
#include "paddle/cinn/adt/equation_function_constants_provider.h"
#include "paddle/cinn/adt/equation_graph.h"
#include "paddle/cinn/adt/m_expr.h"
#include "paddle/cinn/adt/naive_op_equation_context.h"
#include "paddle/cinn/hlir/framework/graph.h"

namespace cinn::adt {

class EquationFunctionConstantsProvider;
class DirectionEquationGenerator;

using EquationCtx4OpStmtT =
    std::function<std::shared_ptr<config::NaiveOpEquationContext>(
        const OpStmt&)>;
using AnchorIndex = Index;

struct AnchorGroup {
  AnchorIndex anchor_index;
  OpStmt op_stmt;
  List<OpStmt> op_stmts;
  EquationCtx4OpStmtT EquationCtx4OpStmt;

  void PrintEquations() const;
};

std::vector<AnchorGroup> PartitionOpStmts(
    const EquationCtx4OpStmtT& EquationCtx4OpStmt,
    const List<OpStmt>& op_stmts,
    const std::shared_ptr<DirectionEquationGenerator>&
        direction_equation_generator);

void CheckEquationSolvable(
    const AnchorGroup& igroup_spec,
    const std::shared_ptr<const EquationFunctionConstantsProvider>&
        constant_provider,
    const std::shared_ptr<DirectionEquationGenerator>&
        direction_equation_generator);

GraphView MakeGlobalEquationGraphViewForPartition(
    const EquationCtx4OpStmtT& EquationCtx4OpStmt,
    const List<OpStmt>& op_stmts,
    const std::shared_ptr<DirectionEquationGenerator>&
        direction_equation_generator);

}  // namespace cinn::adt
