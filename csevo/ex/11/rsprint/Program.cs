// 슬라이드 p11-v10-rs-print — record struct 의 ToString, C# 10.0
using System;

record struct Size(int W, int H);

record struct Box
{
    public string Label;                    // public field: printed
    public Size Size { get; set; }          // nested record struct
    private int secret;                     // private: not printed
    public int Area => Size.W * Size.H;     // readable: printed
    public void Hide(int s) => secret = s;
}

record struct Empty;

class App
{
    static void Main()
    {
        var b = new Box { Label = "tea", Size = new Size(2, 3) };
        b.Hide(42);
        Console.WriteLine(b);
        Console.WriteLine(new Empty());
        Console.WriteLine(default(Box));
    }
}
