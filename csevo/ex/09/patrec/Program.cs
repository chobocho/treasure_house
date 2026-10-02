// 슬라이드 p9-v8-recpat — 재귀 패턴, C# 8.0
using System;

abstract class Expr { }
class Num : Expr
{
    public int V;
    public Num(int v) { V = v; }
    public void Deconstruct(out int v) { v = V; }
    public override string ToString() => V.ToString();
}
class Op : Expr
{
    public char Sym; public Expr L, R;
    public Op(char s, Expr l, Expr r) { Sym = s; L = l; R = r; }
    public void Deconstruct(out char s, out Expr l, out Expr r)
    { s = Sym; l = L; r = R; }
    public override string ToString() => $"({L} {Sym} {R})";
}

class App
{
    // patterns inside patterns, as deep as the data
    static Expr Simplify(Expr e) => e switch
    {
        Op('+', Num(0), var x) => Simplify(x),
        Op('+', var x, Num(0)) => Simplify(x),
        Op('*', Num(1), var x) => Simplify(x),
        Op('*', var x, Num(1)) => Simplify(x),
        Op('*', Num(0), _) => new Num(0),
        Op('+', Num(var a), Num(var b)) => new Num(a + b),
        Op(var s, var l, var r) => new Op(s, Simplify(l), Simplify(r)),
        _ => e,
    };

    static void Main()
    {
        var x = new Num(7);
        Expr e = new Op('*', new Op('+', new Num(0), x), new Num(1));
        Console.WriteLine("{0} => {1}", e, Simplify(e));
        e = new Op('*', new Op('+', new Num(2), new Num(3)),
                        new Op('+', x, new Num(0)));
        Console.WriteLine("{0} => {1}", e, Simplify(e));
    }
}
