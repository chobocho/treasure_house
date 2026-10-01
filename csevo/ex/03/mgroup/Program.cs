// 슬라이드 p3-v2-method-group — 메서드 그룹 변환, C# 2.0
using System;

class App
{
    static void OnClick(object sender, EventArgs e)
    {
        Console.WriteLine("OnClick");
    }

    static void Main()
    {
        EventHandler a = new EventHandler(OnClick);  // the C# 1 form
        EventHandler b = OnClick;                    // the short form
        a(null, EventArgs.Empty);
        b(null, EventArgs.Empty);
        Console.WriteLine(a == b);
    }
}
