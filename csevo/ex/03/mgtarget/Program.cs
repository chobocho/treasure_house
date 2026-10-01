// 슬라이드 p3-v2-mg-target — 메서드 그룹은 대상을 지금 정한다, C# 2.0
using System;

delegate void D();

class Speaker
{
    string name;
    public Speaker(string name) { this.name = name; }
    public void Say() { Console.WriteLine("I am " + name); }
}

class App
{
    static void Main()
    {
        Speaker s = new Speaker("first");
        D group = s.Say;                      // target: this object
        D anon = delegate { s.Say(); };       // reads s at the call
        s = new Speaker("second");
        group();
        anon();

        s = null;
        anon = delegate { s.Say(); };         // fine until called
        try { group = s.Say; }                // throws right here
        catch (Exception e)
        {
            Console.WriteLine(e.GetType().Name + ": " + e.Message);
        }
    }
}
