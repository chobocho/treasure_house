// 슬라이드 p2-v1-goto — goto case 와 goto default, C# 1.0
using System;

class App
{
    static string Price(string size)
    {
        int cents = 0;
        switch (size)
        {
            case "large":
                cents += 100;
                goto case "medium";      // explicit fall-through
            case "medium":
                cents += 50;
                goto default;
            default:
                cents += 300;
                break;
        }
        return size + " " + cents;
    }

    static void Main()
    {
        Console.WriteLine(Price("large"));
        Console.WriteLine(Price("medium"));
        Console.WriteLine(Price("small"));

        int i = 0;
    again:
        i++;
        if (i < 3) goto again;           // plain labels work too
        Console.WriteLine("i = " + i);
    }
}
