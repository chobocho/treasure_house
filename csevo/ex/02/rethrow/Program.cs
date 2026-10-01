// 슬라이드 p2-v1-rethrow — throw; 와 throw e; 의 차이, C# 1.0
using System;
using System.Diagnostics;

class App
{
    static void Parse() { throw new FormatException("bad"); }

    static void Keep()
    {
        try { Parse(); }
        catch (FormatException) { throw; }          // rethrow as is
    }

    static void Reset()
    {
        try { Parse(); }
        catch (FormatException e) { throw e; }      // throws anew
    }

    static void Show(string label, Exception e)
    {
        StackTrace st = new StackTrace(e, false);
        string frames = "";
        for (int i = 0; i < st.FrameCount; i++)
            frames += " " + st.GetFrame(i).GetMethod().Name;
        Console.WriteLine(label + ":" + frames);
    }

    static void Main()
    {
        try { Keep(); } catch (Exception e) { Show("throw;  ", e); }
        try { Reset(); } catch (Exception e) { Show("throw e;", e); }
    }
}
