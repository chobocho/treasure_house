// 슬라이드 p11-v10-ih-bool — bool 을 돌려주는 Append, C# 10.0
using System;
using System.Runtime.CompilerServices;
using System.Text;

[InterpolatedStringHandler]
public ref struct Clip
{
    StringBuilder sb; int max;
    public Clip(int literalLength, int formattedCount, int max)
    {
        sb = new StringBuilder();
        this.max = max;
    }
    public bool AppendLiteral(string s) => Add(s);
    public bool AppendFormatted<T>(T v) => Add(v.ToString());
    bool Add(string s)
    {
        if (sb.Length + s.Length > max)
        {
            sb.Append("...");
            return false;
        }
        sb.Append(s);
        return true;
    }
    public override string ToString() => sb.ToString();
}

class App
{
    static int calls;
    static int Next() { calls++; return calls * 100; }

    static string Head(int max,
        [InterpolatedStringHandlerArgument("max")] Clip text)
        => text.ToString();

    static void Main()
    {
        string t = Head(30, $"a={Next()} b={Next()} c={Next()}");
        Console.WriteLine($"{t}  (Next() ran {calls} times)");
        t = Head(8, $"a={Next()} b={Next()} c={Next()}");
        Console.WriteLine($"{t}  (Next() ran {calls} times)");
    }
}
