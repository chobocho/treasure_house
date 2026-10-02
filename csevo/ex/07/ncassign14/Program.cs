// 슬라이드 p7-v6-nullcond-assign14 — null 조건 대입, C# 14.0
using System;

class Settings
{
    public string Theme = "light";
    public int Saves;
    public event Action Changed;
    public void Raise() { Changed?.Invoke(); }
}

class App
{
    static string Pick(string s)
    {
        Console.WriteLine("  Pick(" + s + ") evaluated");
        return s;
    }

    static void Main()
    {
        Settings on = new Settings(), off = null;
        on?.Theme = Pick("dark");
        off?.Theme = Pick("blue");              // right side skipped
        on?.Saves += 2;
        off?.Saves += 2;
        on?.Changed += () => Console.WriteLine("  changed");
        on?.Raise();
        Console.WriteLine(on.Theme + " " + on.Saves);
#if BAD
        on?.Saves++;
#endif
    }
}
