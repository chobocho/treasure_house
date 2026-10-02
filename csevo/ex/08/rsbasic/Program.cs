// 슬라이드 p8-v7_2-refstruct — ref struct, C# 7.2
using System;

ref struct Window          // may hold a Span<T> field
{
    public Span<int> Items;
    public int Start;

    public Window(Span<int> items, int start)
    {
        Items = items; Start = start;
    }

    public int Sum()
    {
        int s = 0;
        foreach (int x in Items) s += x;
        return s;
    }
}

class App
{
    static void Main()
    {
        int[] data = { 1, 2, 3, 4, 5, 6 };
        var w = new Window(new Span<int>(data, 2, 3), 2);
        Console.WriteLine(w.Sum());        // 3 + 4 + 5
        w.Items[0] = 100;                  // writes into data
        Console.WriteLine(data[2]);
    }
}
