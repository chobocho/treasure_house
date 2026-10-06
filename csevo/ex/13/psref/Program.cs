// 슬라이드 p13-v12-ps-ref — ref struct 와 스팬 매개변수, C# 12.0
using System;

ref struct Window(Span<int> data, int start)
{
    public int First = data[start];          // initializer: allowed
    public Span<int> Rest = data.Slice(start);
    public int Start => start;               // int: captured
#if BAD
    public int Len => data.Length;           // Span: no capture
#endif
}

class App
{
    static void Main()
    {
        Span<int> s = stackalloc int[] { 5, 6, 7, 8 };
        var w = new Window(s, 1);
        Console.WriteLine($"{w.First} {w.Rest.Length} {w.Start}");
    }
}
