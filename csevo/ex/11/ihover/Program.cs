// 슬라이드 p11-v10-ih-over — string 오버로드와 처리기 오버로드, C# 10.0
using System;
using System.Runtime.CompilerServices;
using System.Text;

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
    static void Log(string s) => Console.WriteLine("string  : " + s);
    static void Log(H h)
        => Console.WriteLine("handler : " + h.ToString());

    const string C = "c";

    static void Main()
    {
        string v = "v";
        Log($"plain");
        Log($"{"test"}");
        Log($"{C}!");
        Log($"{1}");
        Log($"{v}");
        Log("x" + v);
    }
}
