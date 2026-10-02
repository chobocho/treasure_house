// 슬라이드 p7-v6-nullcond-once — 받는 쪽은 한 번만 평가, C# 6.0
using System;

class Item { public string Name = "box"; }

class App
{
    static int calls;
    static Item Lookup() { calls++; return new Item(); }

    static void Main()
    {
        calls = 0;
        string a = Lookup() != null ? Lookup().Name : null;
        Console.WriteLine("?: form {0}, Lookup called {1}x", a, calls);

        calls = 0;
        string b = Lookup()?.Name;
        Console.WriteLine("?. form {0}, Lookup called {1}x", b, calls);

        calls = 0;
        Item tmp = Lookup();                       // C# 5 by hand
        string c = tmp != null ? tmp.Name : null;
        Console.WriteLine("temp    {0}, Lookup called {1}x", c, calls);
    }
}
