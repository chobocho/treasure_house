// 슬라이드 p7-v6-nameof-shadow — 매개변수가 바깥 이름을 가림, C# 11.0
using System;

class TagAttribute : Attribute
{
    public readonly string Name;
    public TagAttribute(string name) { Name = name; }
}

class C
{
    class TItem
    {
        internal const string Code = "";
    }

    [Tag(nameof(TItem.Code))]    // class TItem, or type parameter?
    public static void M<TItem>() { }
}

class App
{
    static void Main()
    {
        object[] a =
            typeof(C).GetMethod("M").GetCustomAttributes(false);
        Console.WriteLine(((TagAttribute)a[0]).Name);
    }
}
