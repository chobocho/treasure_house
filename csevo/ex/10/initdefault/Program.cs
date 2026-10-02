// 슬라이드 p10-v9-init-default — init 은 채움을 강제하지 않는다, C# 9.0
using System;

class Order
{
    public string Customer { get; init; }
    public int Quantity { get; init; }
}

record Mail(string To)
{
    public string Subject { get; init; }
}

class App
{
    static void Main()
    {
        var o = new Order { Quantity = 2 };  // Customer forgotten
        Console.WriteLine(o.Customer == null);
        Console.WriteLine(new Order().Quantity);
        Console.WriteLine(new Mail("ann"));   // Subject forgotten
    }
}
