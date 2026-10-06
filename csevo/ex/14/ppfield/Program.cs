// 슬라이드 p14-v13-pp-field — C# 14 의 field 와 만나면, C# 14.0
using System;

partial class Item
{
    public partial string Name { get; set; } = "?";  // initializer
    public partial int Count { get; set; }
}

partial class Item
{
    // the implementing part may use the backing field 'field'
    public partial string Name
    {
        get => field;
        set => field = value.ToUpperInvariant();
    }
    // one accessor may stay automatic, the other needs a body
    public partial int Count { get; set => field = Math.Max(0, value); }
}

class App
{
    static void Main()
    {
        var it = new Item();
        Console.WriteLine(it.Name + " " + it.Count);
        it.Name = "pen";
        it.Count = -5;
        Console.WriteLine(it.Name + " " + it.Count);
    }
}
