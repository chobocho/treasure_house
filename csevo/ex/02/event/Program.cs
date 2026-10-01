// 슬라이드 p2-v1-event — 필드처럼 선언한 이벤트, C# 1.0
using System;

delegate void PriceChanged(string item, decimal price);

class Shop
{
    public event PriceChanged Changed;

    public void SetPrice(string item, decimal price)
    {
        PriceChanged h = Changed;        // C# 1 idiom: copy, test, call
        if (h != null)
            h(item, price);
    }
}

class App
{
    static void Show(string item, decimal p)
    {
        Console.WriteLine("  " + item + " = " + p);
    }

    static void Main()
    {
        Shop shop = new Shop();
        Console.WriteLine("no subscriber:");
        shop.SetPrice("tea", 3.5m);       // nothing happens, no crash
        shop.Changed += new PriceChanged(Show);
        Console.WriteLine("one subscriber:");
        shop.SetPrice("tea", 4.0m);
        shop.Changed -= new PriceChanged(Show);
        shop.SetPrice("tea", 4.5m);
        Console.WriteLine("done");
    }
}
