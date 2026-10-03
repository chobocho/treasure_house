// 슬라이드 p12-v11-ad-lower — 컴파일러가 넣는 기본값 대입, C# 11
using System;

struct S                 // the proposal's examples 1, 2, 4, 5
{
    int x, y;
    public S(int a) { }
    public S(long a) { x = 1; }
    public S(bool b) { if (b) x = 1; else y = 2; }
    public S(string s) { x = 1; if (s != null) M(); y = 2; }
    void M() { }
    public override string ToString() => x + "," + y;
}

class Program
{
    static void Show(string label, Type arg, object value)
    {
        var c = typeof(S).GetConstructor(new[] { arg });
        object made = c.Invoke(new[] { value });
        Console.WriteLine("{0} -> {1}", label, made);
        var ops = Il.Ops(c);
        for (int i = 0; i < ops.Count; i += 6)     // six per line
            Console.WriteLine("    " + string.Join(" | ",
                ops.GetRange(i, Math.Min(6, ops.Count - i))));
    }

    static void Main()
    {
        Show("1: S(int)   ", typeof(int), 0);
        Show("2: S(long)  ", typeof(long), 0L);
        Show("4: S(bool)  ", typeof(bool), true);
        Show("5: S(string)", typeof(string), "m");
    }
}
