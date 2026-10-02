// 슬라이드 p8-v7_1-tuplenames-rules — 이름을 유추하지 않는 경우, C# 7.1
using System;

class P
{
    public int X = 1;
    public int Item2 = 2;    // a field that looks like a tuple name
    public int Rest = 3;
}

class App
{
    static void Main()
    {
        P p = new P(), q = new P();
        string s = " ab ";
        var a = (s.Length, s.Trim());    // Length; a call gets no name
        Console.WriteLine(a.Length + " [" + a.Item2 + "]");
        var b = (p.X, q.X);              // duplicates: both dropped
        Console.WriteLine(b.Item1 + b.Item2);
        var c = (p.Rest, p.Item2);       // reserved names: dropped
        Console.WriteLine(c.Item2);      // position 2, i.e. p.Item2
        var d = (p.Item2, p.Rest);
        Console.WriteLine(d.Item2);      // position 2, i.e. p.Rest!
#if BAD
        var anon = new { p.X, q.X };     // anonymous types refuse
#endif
    }
}
