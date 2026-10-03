// 슬라이드 p11-v10-ih-async — 구멍 안의 await, C# 10.0
using System;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;

[InterpolatedStringHandler]
public ref struct H
{
    StringBuilder sb;
    public H(int literalLength, int formattedCount)
        => sb = new StringBuilder();
    public void AppendLiteral(string s) => sb.Append(s);
    public void AppendFormatted<T>(T v) => sb.Append(v);
    public override string ToString() => sb.ToString();
}

class App
{
    static void Log(H h)
        => Console.WriteLine("handler: " + h.ToString());
    static void Log(string s) => Console.WriteLine("string : " + s);

    static async Task Main()
    {
        int n = 1;
        Log($"n={n}");                          // handler
        string s = $"n={await Task.FromResult(2)}";
        Log(s);                                 // string: built first
#if AWAIT
        Log($"n={await Task.FromResult(3)}");   // CS4007
#endif
    }
}
