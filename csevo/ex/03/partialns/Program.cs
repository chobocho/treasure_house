// 슬라이드 p3-v2-partial-ns — 이름공간을 빠뜨린 조각, C# 2.0
using System;

partial class Order                  // meant to be Shop.Order
{
    public string Name = "pen";
}

class App
{
    static void Main()
    {
        Console.WriteLine(typeof(Shop.Order).FullName);
        Console.WriteLine(typeof(Order).FullName);
        Console.WriteLine(typeof(Shop.Order) == typeof(Order));
        Console.WriteLine(new Shop.Order().Id + " " + new Order().Name);
    }
}
