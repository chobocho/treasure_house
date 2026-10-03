// 슬라이드 p11-v10-st-readonly — readonly struct 의 초기화자, C# 10.0
using System;

readonly struct Range
{
    public int Start { get; } = 0;
    public int End { get; } = 10;           // default range

    public Range() { }                      // runs the initializers
    public Range(int end) { End = end; }

    public override string ToString() => Start + ".." + End;
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Range());
        Console.WriteLine(new Range(3));
        Console.WriteLine(default(Range));
    }
}
