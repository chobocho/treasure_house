// 슬라이드 p11-v10-rs-ctor — record struct 의 다른 생성자, C# 10.0
using System;

record struct Range(int Start, int End)
{
    public Range(int length) : this(0, length) { }   // calls primary
#if BAD
    public Range(string s) : this() { End = s.Length; }
#endif
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Range(5));
        Console.WriteLine(new Range());     // parameterless: all zero
    }
}
