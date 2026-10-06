// 슬라이드 p13-v12-pc-scope — 매개변수를 쓸 수 있는 자리, C# 12.0
using System;

class Base(string tag)
{
    public string Tag = tag;
}

class Item(string name, int qty) : Base(name.ToUpper()) // base args
{
    public int Qty = qty;                               // initializer
    public string Name => name;                         // accessor
    public string Line() => $"{Tag} {name} x{Qty}";     // method
    public string Param => nameof(qty);                 // nameof

    public Item(string name) : this(name, 1)
    {
#if CTOR
        Console.WriteLine(qty);        // another constructor's body
#endif
    }
}

class App
{
    static void Main()
    {
        var i = new Item("pen");
        Console.WriteLine(i.Line() + " " + i.Name + " " + i.Param);
    }
}
