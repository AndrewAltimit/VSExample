using System;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace HelloWorld.Tests
{
    [TestClass]
    public class UnitTest1
    {
        [TestMethod]
        public void TestMethod1()
        {
            Assert.IsTrue(true, "Basic test should pass");
        }

        [TestMethod]
        public void TestDateTime()
        {
            DateTime now = DateTime.Now;
            Assert.IsNotNull(now);
            Assert.IsTrue(now.Year >= 2024);
        }

        [TestMethod]
        public void TestFrameworkVersion()
        {
            Version version = Environment.Version;
            Assert.IsNotNull(version);
            Assert.IsTrue(version.Major >= 4);
        }
    }
}