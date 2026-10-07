// 슬라이드 p15-v14-fk-initacc — init 접근자의 field, C# 14
using System;

record Message
{
    public string Text
    {
        get;
        init => field = value
            ?? throw new ArgumentNullException(nameof(value));
    }
    public string Upper => field ??= Text.ToUpperInvariant();
}

class Program
{
    static void Main()
    {
        var m = new Message { Text = "hi" };
        Console.WriteLine(m.Text + " " + m.Upper);
        var n = m with { Text = "bye" };
        Console.WriteLine(n.Text + " " + n.Upper);
        try { _ = m with { Text = null }; }
        catch (ArgumentNullException e)
        {
            Console.WriteLine("ArgumentNullException: " + e.ParamName);
        }
#if BAD
        m.Text = "x";
#endif
    }
}
