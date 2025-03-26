
// components/Contact.js
import React, { useState } from 'react';

const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Here you would typically send the form data to a server
    alert('Thank you for your message! We will get back to you soon.');
    setFormData({ name: '', email: '', message: '' });
  };

  return (
    <section id="contact" className="contact-section">
      <div className="container">
        <h2 className="section-title">Contact Us</h2>
        <form className="contact-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <input 
              type="text" 
              id="name" 
              name="name" 
              placeholder="Your Name" 
              required 
              value={formData.name}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <input 
              type="email" 
              id="email" 
              name="email" 
              placeholder="Your Email" 
              required 
              value={formData.email}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <textarea 
              id="message" 
              name="message" 
              placeholder="Your Message" 
              required 
              value={formData.message}
              onChange={handleChange}
            ></textarea>
          </div>
          <button type="submit" className="cta-button primary">Send Message</button>
        </form>
      </div>
    </section>
  );
};

export default Contact;
