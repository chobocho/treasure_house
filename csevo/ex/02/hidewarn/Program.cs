// 슬라이드 p2-v1-hidewarn — new 를 빠뜨린 숨김, C# 1.0
using System;

class Base
{
    public void Save() { Console.WriteLine("Base.Save"); }
    public virtual void Load() { Console.WriteLine("Base.Load"); }
}

class Kid : Base
{
    public void Save() { Console.WriteLine("Kid.Save"); }
    public void Load() { Console.WriteLine("Kid.Load"); }
}

class App
{
    static void Main()
    {
        Base b = new Kid();
        b.Save();
        b.Load();     // not an override: the warning says so
    }
}
