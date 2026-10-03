// 슬라이드 p11-v10-ih-index — 인덱서와 처리기, C# 10.0
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

[InterpolatedStringHandler]
public ref struct Key
{
    public string Text;
    public Key(int literalLength, int formattedCount, Table t)
    {
        Console.WriteLine($"  handler sees Count={t.Count}");
        Text = t.Prefix;
    }
    public void AppendLiteral(string s) => Text += s;
    public void AppendFormatted<T>(T v) => Text += v;
}

public class Table
{
    public string Prefix = "k:";
    Dictionary<string, int> d = new Dictionary<string, int>();
    public int Count => d.Count;
    public int this[[InterpolatedStringHandlerArgument("")] Key k]
    {
        get => d[k.Text];
        set { d[k.Text] = value; Console.WriteLine($"  set {k.Text}"); }
    }
}

class App
{
    static void Main()
    {
        var t = new Table();
        t[$"a{1}"] = 10;                       // receiver is ready
        Console.WriteLine($"  get {t[$"a{1}"]}");
#if BAD
        var u = new Table { [$"b{2}"] = 20 };  // object initializer
#endif
    }
}
