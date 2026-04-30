from csveditor.formulas import EvalContext, eval_formula


def test_arithmetic_and_refs():
    data = [["2", "3", "=A1+B1"]]
    ctx = EvalContext(lambda r, c: data[r][c] if r < len(data) and c < len(data[r]) else "")
    assert eval_formula(data[0][2], ctx) == "5"


def test_sum_and_if():
    data = [["10"], ["20"], ["=SUM(A1:A2)"], ["=IF(A1>5,\"H\",\"L\")"]]
    ctx = EvalContext(lambda r, c: data[r][c] if r < len(data) and c < len(data[r]) else "")
    assert eval_formula(data[2][0], ctx) == "30"
    assert eval_formula(data[3][0], ctx) == "H"


def test_cycle():
    data = [["=B1", "=A1"]]
    ctx = EvalContext(lambda r, c: data[r][c])
    assert eval_formula(data[0][0], ctx) == "#CYCLE!"
