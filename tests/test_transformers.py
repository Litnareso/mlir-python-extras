import re
from textwrap import dedent

import pytest

from mlir_utils.ast.canonicalize import transform_func, canonicalize, Canonicalizer
from mlir_utils.dialects.ext.arith import constant
from mlir_utils.dialects.ext.scf import (
    ReplaceYieldWithSCFYield,
    ReplaceSCFCond,
    InsertEndIfs,
    InsertEmptyYield,
    CheckMatchingYields,
    InsertPreElses,
    unstack_if,
    RemoveJumpsAndInsertGlobals,
    yield_,
    unstack_end_branch,
    unstack_else,
    unstack_else_if,
)

# noinspection PyUnresolvedReferences
from mlir_utils.testing import mlir_ctx as ctx, filecheck, MLIRContext
from mlir_utils.types import _placeholder_opaque_t

# needed since the fix isn't defined here nor conftest.py
pytest.mark.usefixtures("ctx")


def test_if_replace_yield(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            yield
        return

    code = transform_func(iffoo, ReplaceYieldWithSCFYield).code

    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            yield_()
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)

    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
        return

    code = transform_func(iffoo, InsertEmptyYield).code

    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0); yield
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)

    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            res = yield three
        return

    code = transform_func(iffoo, ReplaceYieldWithSCFYield).code

    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            res = yield_(three)
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)

    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            res1, res2 = yield three, three
        return

    code = transform_func(iffoo, ReplaceYieldWithSCFYield).code

    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            res1, res2 = yield_(three, three)
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)

    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            res1, res2, res3 = yield three, three, three
        return

    code = transform_func(iffoo, ReplaceYieldWithSCFYield).code

    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            res1, res2, res3 = yield_(three, three, three)
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_if_replace_cond(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            yield
        return

    code = transform_func(iffoo, ReplaceYieldWithSCFYield, ReplaceSCFCond).code

    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if __unstack_if__144 := unstack_if(one < two, ()):
            three = constant(3.0)
            yield_()
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)

    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            res = yield three
        return

    code = transform_func(iffoo, ReplaceYieldWithSCFYield, ReplaceSCFCond).code

    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if __unstack_if__167 := unstack_if(one < two, (_placeholder_opaque_t(),)):
            three = constant(3.0)
            res = yield_(three)
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)

    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            res1, res2 = yield three, three
        return

    code = transform_func(iffoo, ReplaceYieldWithSCFYield, ReplaceSCFCond).code

    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if __unstack_if__190 := unstack_if(one < two, (_placeholder_opaque_t(), _placeholder_opaque_t())):
            three = constant(3.0)
            res1, res2 = yield_(three, three)
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)

    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            res1, res2, res3 = yield three, three, three
        return

    code = transform_func(iffoo, ReplaceYieldWithSCFYield, ReplaceSCFCond).code

    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if __unstack_if__213 := unstack_if(one < two, (_placeholder_opaque_t(), _placeholder_opaque_t(), _placeholder_opaque_t())):
            three = constant(3.0)
            res1, res2, res3 = yield_(three, three, three)
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_insert_end_ifs(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            yield
        return

    code = transform_func(
        iffoo,
        ReplaceYieldWithSCFYield,
        ReplaceSCFCond,
        InsertEndIfs,
    ).code
    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if __unstack_if__238 := unstack_if(one < two, ()):
            three = constant(3.0)
            yield_(); __unstack_if__238 = unstack_end_branch(__unstack_if__238)
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)

    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            yield three
        else:
            four = constant(4.0)
            yield four
        return

    code = transform_func(
        iffoo,
        ReplaceYieldWithSCFYield,
        ReplaceSCFCond,
        InsertEndIfs,
    ).code
    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if __unstack_if__266 := unstack_if(one < two, (_placeholder_opaque_t(),)):
            three = constant(3.0)
            yield_(three); __unstack_if__266 = unstack_end_branch(__unstack_if__266)
        else:
            four = constant(4.0)
            yield_(four); __unstack_if__266 = unstack_end_branch(__unstack_if__266)
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_if_nested_no_else_no_yield(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            if one < two:
                four = constant(4.0)
            yield
        return

    iffoo()

    code = transform_func(iffoo, InsertEmptyYield).code
    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            if one < two:
                four = constant(4.0); yield
            yield
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_if_nested_with_else_no_yield(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            if one < two:
                four = constant(4.0)
            else:
                five = constant(5.0)
            yield
        return

    iffoo()

    code = transform_func(iffoo, InsertEmptyYield).code
    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            if one < two:
                four = constant(4.0); yield
            else:
                five = constant(5.0); yield
            yield
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_insert_end_ifs_yield(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            yield
        else:
            four = constant(4.0)
            yield
        return

    code = transform_func(
        iffoo, ReplaceYieldWithSCFYield, ReplaceSCFCond, InsertEndIfs
    ).code
    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if __unstack_if__362 := unstack_if(one < two, ()):
            three = constant(3.0)
            yield_(); __unstack_if__362 = unstack_end_branch(__unstack_if__362)
        else:
            four = constant(4.0)
            yield_(); __unstack_if__362 = unstack_end_branch(__unstack_if__362)
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_if_else_with_nested_no_yields_yield_results(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            if two < three:
                four = constant(4.0)
            res = yield three
        else:
            five = constant(5.0)
            res = yield five
        return

    code = transform_func(
        iffoo,
        InsertEmptyYield,
        ReplaceYieldWithSCFYield,
        ReplaceSCFCond,
    ).code
    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if __unstack_if__394 := unstack_if(one < two, (_placeholder_opaque_t(),)):
            three = constant(3.0)
            if __unstack_if__396 := unstack_if(two < three, ()):
                four = constant(4.0); yield_()
            res = yield_(three)
        else:
            five = constant(5.0)
            res = yield_(five)
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_if_else_with_nested_no_yields_yield_multiple_results(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            if two < three:
                four = constant(4.0)
            res = yield three, three
        else:
            five = constant(5.0)
            res = yield five, five
        return

    code = transform_func(
        iffoo,
        InsertEmptyYield,
        ReplaceYieldWithSCFYield,
    ).code
    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        if one < two:
            three = constant(3.0)
            if two < three:
                four = constant(4.0); yield_()
            res = yield_(three, three)
        else:
            five = constant(5.0)
            res = yield_(five, five)
        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_if_nested_with_else_no_yield_insert_order(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)

        if one < two:
            three = constant(3.0)
            if one < two:
                four = constant(4.0)
            else:
                five = constant(5.0)
            yield

        return

    iffoo()

    code = transform_func(
        iffoo,
        InsertEmptyYield,
        # ReplaceYieldWithSCFYield,
        # ReplaceSCFCond,
        # InsertEndIfs,
    ).code
    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)

        if one < two:
            three = constant(3.0)
            if one < two:
                four = constant(4.0); yield
            else:
                five = constant(5.0); yield
            yield

        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_if_else_with_nested_no_yields_insert_order(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)

        if one < two:
            three = constant(3.0)
            if one < two:
                four = constant(4.0)
            yield
        else:
            five = constant(5.0)

        return

    iffoo()
    code = transform_func(
        iffoo,
        InsertEmptyYield,
        ReplaceYieldWithSCFYield,
        # ReplaceSCFCond,
        # InsertEndIfs,
    ).code
    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)

        if one < two:
            three = constant(3.0)
            if one < two:
                four = constant(4.0); yield_()
            yield_()
        else:
            five = constant(5.0); yield_()

        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_if_nested_with_else_no_yields_insert_order(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)

        if one < two:
            three = constant(3.0)
            if one < two:
                four = constant(4.0)
            else:
                five = constant(5.0)
            yield
        else:
            six = constant(6.0)

        return

    iffoo()
    code = transform_func(
        iffoo,
        InsertEmptyYield,
        ReplaceYieldWithSCFYield,
        # ReplaceSCFCond,
        # InsertEndIfs,
    ).code
    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)

        if one < two:
            three = constant(3.0)
            if one < two:
                four = constant(4.0); yield_()
            else:
                five = constant(5.0); yield_()
            yield_()
        else:
            six = constant(6.0); yield_()

        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_if_with_else_else_with_yields(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)

        if one < two:
            three = constant(3.0)
            yield
        else:
            if one < two:
                four = constant(4.0)
                yield
            else:
                five = constant(5.0)
                yield
            yield

        return

    try:
        code = transform_func(
            iffoo,
            InsertEmptyYield,
            ReplaceYieldWithSCFYield,
            CheckMatchingYields,
            # ReplaceSCFCond,
            # InsertEndIfs,
        )
    except AssertionError as e:
        assert e.args[0].startswith(
            "unmatched if/elses and yields: n_ifs=2 n_elses=2 n_yields=3; line"
        )

    def iffoo():
        one = constant(1.0)
        two = constant(2.0)

        if one < two:
            three = constant(3.0)
            yield
        else:
            if one < two:
                four = constant(4.0)
                yield
            else:
                five = constant(5.0)
                yield
            yield

        return

    code = transform_func(
        iffoo,
        InsertEmptyYield,
        ReplaceYieldWithSCFYield,
        CheckMatchingYields,
        ReplaceSCFCond,
        InsertEndIfs,
        InsertPreElses,
    ).code

    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)

        if __unstack_if__631 := unstack_if(one < two, ()):
            three = constant(3.0)
            yield_(); __unstack_if__631 = unstack_end_branch(__unstack_if__631); __unstack_if__631 = unstack_else(__unstack_if__631)
        else:
            if __unstack_if__635 := unstack_if(one < two, ()):
                four = constant(4.0)
                yield_(); __unstack_if__635 = unstack_end_branch(__unstack_if__635); __unstack_if__635 = unstack_else(__unstack_if__635)
            else:
                five = constant(5.0)
                yield_(); __unstack_if__635 = unstack_end_branch(__unstack_if__635)
            yield_(); __unstack_if__631 = unstack_end_branch(__unstack_if__631)

        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_if_insert_yields_if_else(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)

        if one < two:
            three = constant(3.0)
        else:
            if one < two:
                four = constant(4.0)
            else:
                five = constant(5.0)
            yield

        return

    code = transform_func(
        iffoo,
        InsertEmptyYield,
        ReplaceYieldWithSCFYield,
        CheckMatchingYields,
        ReplaceSCFCond,
        InsertEndIfs,
        InsertPreElses,
    ).code

    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)

        if __unstack_if__684 := unstack_if(one < two, ()):
            three = constant(3.0); yield_(); __unstack_if__684 = unstack_end_branch(__unstack_if__684); __unstack_if__684 = unstack_else(__unstack_if__684)
        else:
            if __unstack_if__687 := unstack_if(one < two, ()):
                four = constant(4.0); yield_(); __unstack_if__687 = unstack_end_branch(__unstack_if__687); __unstack_if__687 = unstack_else(__unstack_if__687)
            else:
                five = constant(5.0); yield_(); __unstack_if__687 = unstack_end_branch(__unstack_if__687)
            yield_(); __unstack_if__684 = unstack_end_branch(__unstack_if__684)

        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_if_canonicalize_elif(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        three = constant(3.0)

        if one < two:
            four = constant(4.0)
            yield
        else:
            if two < three:
                five = constant(5.0)
                yield
            else:
                six = constant(6.0)
                yield
            yield

        return

    code = transform_func(
        iffoo,
        InsertEmptyYield,
        ReplaceYieldWithSCFYield,
        CheckMatchingYields,
        ReplaceSCFCond,
        InsertEndIfs,
        InsertPreElses,
    ).code
    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        three = constant(3.0)

        if __unstack_if__748 := unstack_if(one < two, ()):
            four = constant(4.0)
            yield_(); __unstack_if__748 = unstack_end_branch(__unstack_if__748); __unstack_if__748 = unstack_else(__unstack_if__748)
        else:
            if __unstack_if__752 := unstack_if(two < three, ()):
                five = constant(5.0)
                yield_(); __unstack_if__752 = unstack_end_branch(__unstack_if__752); __unstack_if__752 = unstack_else(__unstack_if__752)
            else:
                six = constant(6.0)
                yield_(); __unstack_if__752 = unstack_end_branch(__unstack_if__752)
            yield_(); __unstack_if__748 = unstack_end_branch(__unstack_if__748)

        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


def test_if_canonicalize_elif_elif(ctx: MLIRContext):
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        three = constant(3.0)

        if one < two:
            four = constant(4.0)
        else:
            if two < three:
                five = constant(5.0)
            else:
                if two < three:
                    six = constant(6.0)
                else:
                    seven = constant(7.0)
                yield
            yield

        return

    code = transform_func(
        iffoo,
        InsertEmptyYield,
        ReplaceYieldWithSCFYield,
        CheckMatchingYields,
        ReplaceSCFCond,
        InsertEndIfs,
        InsertPreElses,
    ).code
    correct = dedent(
        """\
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        three = constant(3.0)

        if __unstack_if__802 := unstack_if(one < two, ()):
            four = constant(4.0); yield_(); __unstack_if__802 = unstack_end_branch(__unstack_if__802); __unstack_if__802 = unstack_else(__unstack_if__802)
        else:
            if __unstack_if__805 := unstack_if(two < three, ()):
                five = constant(5.0); yield_(); __unstack_if__805 = unstack_end_branch(__unstack_if__805); __unstack_if__805 = unstack_else(__unstack_if__805)
            else:
                if __unstack_if__808 := unstack_if(two < three, ()):
                    six = constant(6.0); yield_(); __unstack_if__808 = unstack_end_branch(__unstack_if__808); __unstack_if__808 = unstack_else(__unstack_if__808)
                else:
                    seven = constant(7.0); yield_(); __unstack_if__808 = unstack_end_branch(__unstack_if__808)
                yield_(); __unstack_if__805 = unstack_end_branch(__unstack_if__805)
            yield_(); __unstack_if__802 = unstack_end_branch(__unstack_if__802)

        return
    """
    )
    assert re.sub(r"_\d+", "", correct) == re.sub(r"_\d+", "", code)


class OnlyJumpsCanonicalizer(Canonicalizer):
    cst_transformers = []

    bytecode_patchers = [RemoveJumpsAndInsertGlobals]


only_jumps_canonicalizer = OnlyJumpsCanonicalizer()


def test_unstack_1(ctx: MLIRContext):
    ## fmt: off
    ## @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3)
            yield_()
            ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        ips, ifop = ips_ifop_1
        assert len(ips) == 0

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_2(ctx: MLIRContext):
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3)
            yield_()
            ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        else:
            ips_ifop_1 = unstack_else(ips_ifop_1)
            four = constant(4)
            yield_()
            ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        ips, ifop = ips_ifop_1
        assert len(ips) == 0

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      } else {
        %c4_i64 = arith.constant 4 : i64
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_3(ctx: MLIRContext):
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3)
            yield_()
            ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        elif ips_ifop_2 := unstack_else_if(ips_ifop_1, one < two):
            three = constant(4)
            yield_()
            ips_ifop_2 = unstack_end_branch(ips_ifop_2)
            yield_()
            ips_ifop_2 = unstack_end_branch(ips_ifop_2)
        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      } else {
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c4_i64 = arith.constant 4 : i64
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_4(ctx: MLIRContext):
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3)
            yield_()
            ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        elif ips_ifop_2 := unstack_else_if(ips_ifop_1, one < two):
            three = constant(4)
            yield_()
            ips_ifop_2 = unstack_end_branch(ips_ifop_2)
        else:
            ips_ifop_2 = unstack_else(ips_ifop_2)
            three = constant(5)
            yield_()
            ips_ifop_2 = unstack_end_branch(ips_ifop_2)
            yield_()
            ips_ifop_2 = unstack_end_branch(ips_ifop_2)

        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      } else {
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c4_i64 = arith.constant 4 : i64
        } else {
          %c5_i64 = arith.constant 5 : i64
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_5(ctx: MLIRContext):
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3)
            yield_()
            ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        elif ips_ifop_2 := unstack_else_if(ips_ifop_1, one < two):
            three = constant(4)
            yield_()
            ips_ifop_2 = unstack_end_branch(ips_ifop_2)
        elif ips_ifop_3 := unstack_else_if(ips_ifop_2, one < two):
            three = constant(5)
            yield_()
            ips_ifop_3 = unstack_end_branch(ips_ifop_3)
            yield_()
            ips_ifop_3 = unstack_end_branch(ips_ifop_3)
            yield_()
            ips_ifop_3 = unstack_end_branch(ips_ifop_3)

        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0
        ips, ifop = ips_ifop_3
        assert len(ips) == 0

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      } else {
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c4_i64 = arith.constant 4 : i64
        } else {
          %2 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
          scf.if %2 {
            %c5_i64 = arith.constant 5 : i64
          }
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_6(ctx: MLIRContext):
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3)
            yield_()
            ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        elif ips_ifop_2 := unstack_else_if(ips_ifop_1, one < two):
            three = constant(4)
            yield_()
            ips_ifop_2 = unstack_end_branch(ips_ifop_2)
        elif ips_ifop_3 := unstack_else_if(ips_ifop_2, one < two):
            three = constant(5)
            yield_()
            ips_ifop_3 = unstack_end_branch(ips_ifop_3)
        else:
            ips_ifop_3 = unstack_else(ips_ifop_3)
            three = constant(6)
            yield_()
            ips_ifop_3 = unstack_end_branch(ips_ifop_3)
            yield_()
            ips_ifop_3 = unstack_end_branch(ips_ifop_3)
            yield_()
            ips_ifop_3 = unstack_end_branch(ips_ifop_3)

        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0
        ips, ifop = ips_ifop_3
        assert len(ips) == 0

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      } else {
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c4_i64 = arith.constant 4 : i64
        } else {
          %2 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
          scf.if %2 {
            %c5_i64 = arith.constant 5 : i64
          } else {
            %c6_i64 = arith.constant 6 : i64
          }
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_1_semicolon(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3); yield_(); ips_ifop_1 = unstack_end_branch(ips_ifop_1)

        ips, ifop = ips_ifop_1
        assert len(ips) == 0
    # fmt: on
    # @formatter:on

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_2_semicolon(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3); yield_(); ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        else:
            ips_ifop_1 = unstack_else(ips_ifop_1); four = constant(4); yield_(); ips_ifop_1 = unstack_end_branch(ips_ifop_1)

        ips, ifop = ips_ifop_1
        assert len(ips) == 0
    # fmt: on
    # @formatter:on

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      } else {
        %c4_i64 = arith.constant 4 : i64
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_3_semicolon(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3); yield_(); ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        elif ips_ifop_2 := unstack_else_if(ips_ifop_1, one < two):
            three = constant(4); yield_(); ips_ifop_2 = unstack_end_branch(ips_ifop_2); yield_(); ips_ifop_2 = unstack_end_branch(ips_ifop_2)
        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0
    # fmt: on
    # @formatter:on

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      } else {
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c4_i64 = arith.constant 4 : i64
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_4_semicolon(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3); yield_(); ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        elif ips_ifop_2 := unstack_else_if(ips_ifop_1, one < two):
            three = constant(4); yield_(); ips_ifop_2 = unstack_end_branch(ips_ifop_2); ips_ifop_2 = unstack_else(ips_ifop_2)
        else:
            three = constant(5); yield_(); ips_ifop_2 = unstack_end_branch(ips_ifop_2); yield_(); ips_ifop_2 = unstack_end_branch(ips_ifop_2)

        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0
    # fmt: on
    # @formatter:on

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      } else {
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c4_i64 = arith.constant 4 : i64
        } else {
          %c5_i64 = arith.constant 5 : i64
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_5_semicolon(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3); yield_(); ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        elif ips_ifop_2 := unstack_else_if(ips_ifop_1, one < two):
            three = constant(4); yield_(); ips_ifop_2 = unstack_end_branch(ips_ifop_2)
        elif ips_ifop_3 := unstack_else_if(ips_ifop_2, one < two):
            three = constant(5); yield_(); ips_ifop_3 = unstack_end_branch(ips_ifop_3); yield_(); ips_ifop_3 = unstack_end_branch(ips_ifop_3); yield_(); ips_ifop_3 = unstack_end_branch(ips_ifop_3)

        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0
        ips, ifop = ips_ifop_3
        assert len(ips) == 0
    # fmt: on
    # @formatter:on

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      } else {
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c4_i64 = arith.constant 4 : i64
        } else {
          %2 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
          scf.if %2 {
            %c5_i64 = arith.constant 5 : i64
          }
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_6_semicolon(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3); yield_(); ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        elif ips_ifop_2 := unstack_else_if(ips_ifop_1, one < two):
            three = constant(4); yield_(); ips_ifop_2 = unstack_end_branch(ips_ifop_2)
        elif ips_ifop_3 := unstack_else_if(ips_ifop_2, one < two):
            three = constant(5); yield_(); ips_ifop_3 = unstack_end_branch(ips_ifop_3); ips_ifop_3 = unstack_else(ips_ifop_3)
        else:
            three = constant(6); yield_(); ips_ifop_3 = unstack_end_branch(ips_ifop_3); yield_(); ips_ifop_3 = unstack_end_branch(ips_ifop_3); yield_(); ips_ifop_3 = unstack_end_branch(ips_ifop_3)

        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0
        ips, ifop = ips_ifop_3
        assert len(ips) == 0

    # fmt: on
    # @formatter:on

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      } else {
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c4_i64 = arith.constant 4 : i64
        } else {
          %2 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
          scf.if %2 {
            %c5_i64 = arith.constant 5 : i64
          } else {
            %c6_i64 = arith.constant 6 : i64
          }
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_6_semicolon_move_to_last_elif(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(3); yield_(); ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        elif ips_ifop_2 := unstack_else_if(ips_ifop_1, one < two):
            three = constant(4); yield_(); ips_ifop_2 = unstack_end_branch(ips_ifop_2)
        elif ips_ifop_3 := unstack_else_if(ips_ifop_2, one < two):
            three = constant(5); yield_(); ips_ifop_3 = unstack_end_branch(ips_ifop_3); ips_ifop_3 = unstack_else(ips_ifop_3)
        else:
            three = constant(6); yield_(); ips_ifop_3 = unstack_end_branch(ips_ifop_3); yield_(); ips_ifop_3 = unstack_end_branch(ips_ifop_3); yield_(); ips_ifop_3 = unstack_end_branch(ips_ifop_3)

        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0
        ips, ifop = ips_ifop_3
        assert len(ips) == 0

    # fmt: on
    # @formatter:on

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c3_i64 = arith.constant 3 : i64
      } else {
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c4_i64 = arith.constant 4 : i64
        } else {
          %2 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
          scf.if %2 {
            %c5_i64 = arith.constant 5 : i64
          } else {
            %c6_i64 = arith.constant 6 : i64
          }
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_nested_1(ctx: MLIRContext):
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            if ips_ifop_2 := unstack_if(one < two):
                three = constant(3)
                yield_()
                ips_ifop_2 = unstack_end_branch(ips_ifop_2)
            three = constant(4)
            yield_()
            ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c3_i64 = arith.constant 3 : i64
        }
        %c4_i64 = arith.constant 4 : i64
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_nested_2(ctx: MLIRContext):
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(4)
            if ips_ifop_2 := unstack_if(one < two):
                three = constant(3)
                yield_()
                ips_ifop_2 = unstack_end_branch(ips_ifop_2)
            yield_()
            ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c4_i64 = arith.constant 4 : i64
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c3_i64 = arith.constant 3 : i64
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_nested_1_semicolon(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            if ips_ifop_2 := unstack_if(one < two):
                three = constant(3); yield_(); ips_ifop_2 = unstack_end_branch(ips_ifop_2)
            three = constant(4); yield_(); ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0
    # fmt: on
    # @formatter:on

    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c3_i64 = arith.constant 3 : i64
        }
        %c4_i64 = arith.constant 4 : i64
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_nested_2_semicolon(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            three = constant(4)
            if ips_ifop_2 := unstack_if(one < two):
                three = constant(3); yield_(); ips_ifop_2 = unstack_end_branch(ips_ifop_2); yield_(); ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0

    # fmt: on
    # @formatter:on
    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c4_i64 = arith.constant 4 : i64
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c3_i64 = arith.constant 3 : i64
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_unstack_nested_2_with_else_semicolon(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1)
        two = constant(2)
        if ips_ifop_1 := unstack_if(one < two):
            four = constant(4); yield_(); ips_ifop_1 = unstack_end_branch(ips_ifop_1); ips_ifop_1 = unstack_else(ips_ifop_1)
        else:
            if ips_ifop_2 := unstack_if(one < two):
                three = constant(3); yield_(); ips_ifop_2 = unstack_end_branch(ips_ifop_2); yield_(); ips_ifop_1 = unstack_end_branch(ips_ifop_1)
        ips, ifop = ips_ifop_1
        assert len(ips) == 0
        ips, ifop = ips_ifop_2
        assert len(ips) == 0

    # fmt: on
    # @formatter:on
    iffoo()
    correct = dedent(
        """\
    module {
      %c1_i64 = arith.constant 1 : i64
      %c2_i64 = arith.constant 2 : i64
      %0 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
      scf.if %0 {
        %c4_i64 = arith.constant 4 : i64
      } else {
        %1 = arith.cmpi ult, %c1_i64, %c2_i64 : i64
        scf.if %1 {
          %c3_i64 = arith.constant 3 : i64
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_if_with_results_no_sugar(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        three = constant(3.0)

        if __unstack_if__1125 := unstack_if(one < two, (_placeholder_opaque_t(),)):
            four = constant(4.0)
            res = yield_(four); __unstack_if__1125 = unstack_end_branch(__unstack_if__1125)
        elif __unstack_if__1128 := unstack_else_if(__unstack_if__1125, two < three, (_placeholder_opaque_t(),)):
            five = constant(5.0)
            res1 = yield_(five); __unstack_if__1128 = unstack_end_branch(__unstack_if__1128); __unstack_if__1128 = unstack_else(__unstack_if__1128)
        else:
            six = constant(6.0)
            res2 = yield_(six); __unstack_if__1128 = unstack_end_branch(__unstack_if__1128); res = yield_(res2); __unstack_if__1125 = unstack_end_branch(__unstack_if__1125)

        return
    # fmt: on
    # @formatter:on

    iffoo()
    ctx.module.operation.verify()
    correct = dedent(
        """\
    module {
      %cst = arith.constant 1.000000e+00 : f64
      %cst_0 = arith.constant 2.000000e+00 : f64
      %cst_1 = arith.constant 3.000000e+00 : f64
      %0 = arith.cmpf olt, %cst, %cst_0 : f64
      %1 = scf.if %0 -> (f64) {
        %cst_2 = arith.constant 4.000000e+00 : f64
        scf.yield %cst_2 : f64
      } else {
        %2 = arith.cmpf olt, %cst_0, %cst_1 : f64
        %3 = scf.if %2 -> (f64) {
          %cst_2 = arith.constant 5.000000e+00 : f64
          scf.yield %cst_2 : f64
        } else {
          %cst_2 = arith.constant 6.000000e+00 : f64
          scf.yield %cst_2 : f64
        }
        scf.yield %3 : f64
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_if_with_results_no_sugar_long(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)
        three = constant(3.0)

        if __unstack_if__1176 := unstack_if(one < two, (_placeholder_opaque_t(),)):
            four = constant(4.0)
            res = yield_(four); __unstack_if__1176 = unstack_end_branch(__unstack_if__1176)
        elif __unstack_if__1179 := unstack_else_if(__unstack_if__1176, two < three, (_placeholder_opaque_t(),)):
            five = constant(5.0)
            res1 = yield_(five); __unstack_if__1179 = unstack_end_branch(__unstack_if__1179)
        elif __unstack_if__1182 := unstack_else_if(__unstack_if__1179, two < three, (_placeholder_opaque_t(),)):
            five = constant(6.0)
            res2 = yield_(five); __unstack_if__1182 = unstack_end_branch(__unstack_if__1182)
        elif __unstack_if__1185 := unstack_else_if(__unstack_if__1182, two < three, (_placeholder_opaque_t(),)):
            five = constant(7.0)
            res3 = yield_(five); __unstack_if__1185 = unstack_end_branch(__unstack_if__1185)
        elif __unstack_if__1188 := unstack_else_if(__unstack_if__1185, two < three, (_placeholder_opaque_t(),)):
            five = constant(8.0)
            res4 = yield_(five); __unstack_if__1188 = unstack_end_branch(__unstack_if__1188)
        elif __unstack_if__1191 := unstack_else_if(__unstack_if__1188, two < three, (_placeholder_opaque_t(),)):
            five = constant(9.0)
            res5 = yield_(five); __unstack_if__1191 = unstack_end_branch(__unstack_if__1191); __unstack_if__1191 = unstack_else(__unstack_if__1191)
        else:
            six = constant(10.0)
            res6 = yield_(six); __unstack_if__1191 = unstack_end_branch(__unstack_if__1191); yield_(res5); __unstack_if__1188 = unstack_end_branch(__unstack_if__1188); yield_(res4); __unstack_if__1185 = unstack_end_branch(__unstack_if__1185); yield_(res3); __unstack_if__1182 = unstack_end_branch(__unstack_if__1182); yield_(res2); __unstack_if__1179 = unstack_end_branch(__unstack_if__1179); yield_(res1); __unstack_if__1176 = unstack_end_branch(__unstack_if__1176)

        return
    # fmt: on
    # @formatter:on

    iffoo()
    ctx.module.operation.verify()
    correct = dedent(
        """\
    module {
      %cst = arith.constant 1.000000e+00 : f64
      %cst_0 = arith.constant 2.000000e+00 : f64
      %cst_1 = arith.constant 3.000000e+00 : f64
      %0 = arith.cmpf olt, %cst, %cst_0 : f64
      %1 = scf.if %0 -> (f64) {
        %cst_2 = arith.constant 4.000000e+00 : f64
        scf.yield %cst_2 : f64
      } else {
        %2 = arith.cmpf olt, %cst_0, %cst_1 : f64
        %3 = scf.if %2 -> (f64) {
          %cst_2 = arith.constant 5.000000e+00 : f64
          scf.yield %cst_2 : f64
        } else {
          %4 = arith.cmpf olt, %cst_0, %cst_1 : f64
          %5 = scf.if %4 -> (f64) {
            %cst_2 = arith.constant 6.000000e+00 : f64
            scf.yield %cst_2 : f64
          } else {
            %6 = arith.cmpf olt, %cst_0, %cst_1 : f64
            %7 = scf.if %6 -> (f64) {
              %cst_2 = arith.constant 7.000000e+00 : f64
              scf.yield %cst_2 : f64
            } else {
              %8 = arith.cmpf olt, %cst_0, %cst_1 : f64
              %9 = scf.if %8 -> (f64) {
                %cst_2 = arith.constant 8.000000e+00 : f64
                scf.yield %cst_2 : f64
              } else {
                %10 = arith.cmpf olt, %cst_0, %cst_1 : f64
                %11 = scf.if %10 -> (f64) {
                  %cst_2 = arith.constant 9.000000e+00 : f64
                  scf.yield %cst_2 : f64
                } else {
                  %cst_2 = arith.constant 1.000000e+01 : f64
                  scf.yield %cst_2 : f64
                }
                scf.yield %11 : f64
              }
              scf.yield %9 : f64
            }
            scf.yield %7 : f64
          }
          scf.yield %5 : f64
        }
        scf.yield %3 : f64
      }
    }
    """
    )
    filecheck(correct, ctx.module)


def test_if_with_else_else_with_yields_explicit(ctx: MLIRContext):
    # fmt: off
    # @formatter:off
    @canonicalize(using=only_jumps_canonicalizer)
    def iffoo():
        one = constant(1.0)
        two = constant(2.0)

        if __unstack_if__642 := unstack_if(one < two, ()):
            three = constant(3.0); yield_(); __unstack_if__642 = unstack_end_branch(__unstack_if__642); __unstack_if__642 = unstack_else(__unstack_if__642)
        else:
            if __unstack_if__645 := unstack_if(one < two, ()):
                four = constant(4.0); yield_(); __unstack_if__645 = unstack_end_branch(__unstack_if__645); __unstack_if__645 = unstack_else(__unstack_if__645)
            else:
                five = constant(5.0); yield_(); __unstack_if__645 = unstack_end_branch(__unstack_if__645); yield_(); __unstack_if__642 = unstack_end_branch(__unstack_if__642)

        return
    # fmt: on
    # @formatter:on

    iffoo()
    ctx.module.operation.verify()
    correct = dedent(
        """\
    module {
      %cst = arith.constant 1.000000e+00 : f64
      %cst_0 = arith.constant 2.000000e+00 : f64
      %0 = arith.cmpf olt, %cst, %cst_0 : f64
      scf.if %0 {
        %cst_1 = arith.constant 3.000000e+00 : f64
      } else {
        %1 = arith.cmpf olt, %cst, %cst_0 : f64
        scf.if %1 {
          %cst_1 = arith.constant 4.000000e+00 : f64
        } else {
          %cst_1 = arith.constant 5.000000e+00 : f64
        }
      }
    }
    """
    )
    filecheck(correct, ctx.module)
