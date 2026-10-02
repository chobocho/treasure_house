// 슬라이드 p7-v6-nullcond-coalesce — ?. 와 ?? 그리고 bool?, C# 6.0
using System;

class Order
{
    public string Note;
    public bool Paid;
}

class App
{
    static void Show(Order o)
    {
        int len = o?.Note?.Length ?? 0;        // default when null
        string note = o?.Note ?? "(none)";
        bool paid = o?.Paid ?? false;
        Console.WriteLine("{0} {1} {2} {3}",
            len, note, paid, o?.Paid == true);
#if BAD
        if (o?.Paid) Console.WriteLine("paid");
#endif
    }

    static void Main()
    {
        Show(new Order { Note = "rush", Paid = true });
        Show(new Order());
        Show(null);
    }
}
