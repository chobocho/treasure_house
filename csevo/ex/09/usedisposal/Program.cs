// 슬라이드 p9-v8-disposal — ref struct 의 Dispose 패턴, C# 8.0
using System;

ref struct Lease                     // cannot implement IDisposable
{
    Span<byte> buf;
    public Lease(Span<byte> b) { buf = b; Console.WriteLine("lease"); }
    public int Length => buf.Length;
    public void Dispose()
    {
        buf.Clear();
        Console.WriteLine("return");
    }
}

struct Plain                         // not a ref struct
{
    public void Dispose() => Console.WriteLine("never");
}

class App
{
    static void Main()
    {
        Span<byte> mem = stackalloc byte[8];
        using (var a = new Lease(mem))
            Console.WriteLine("  using statement, " + a.Length);
        using var b = new Lease(mem[..4]);
        Console.WriteLine("  using declaration, " + b.Length);
#if BAD
        using var p = new Plain();   // the pattern is for ref structs
#endif
    }
}
