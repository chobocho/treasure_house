// 슬라이드 p11-v10-pp-bad — 점 경로에 쓸 수 없는 것, C# 10.0
using System;

class Item
{
    public string Name = "pen";
    public string Upper() => Name.ToUpperInvariant();
    public int[] Codes = { 7, 8 };
}

class App
{
    static void Main()
    {
        object o = new Item();
        Console.WriteLine(o is Item { Name.Length: 3 });
        Console.WriteLine(o is Item { Codes.Length: 2 });
#if BAD
        Console.WriteLine(o is Item { Name?.Length: 3 });
        Console.WriteLine(o is { Item.Name: "pen" });
#endif
#if CALL
        Console.WriteLine(o is Item { Upper().Length: 3 });
#endif
    }
}
